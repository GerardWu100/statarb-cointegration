---
title: "Quand une stratégie de cointégration échoue à son propre test"
description: "Un backtest causal sur KO et PEP avec test formel du résidu, positions cohérentes avec le bêta, coûts explicites et valorisation quotidienne."
date: 2026-07-13
image: images/cover-cointegration-regime-break.png
categories: ["Quantitative Research", "Risk Management"]
---

# Quand une stratégie de cointégration échoue à son propre test

Coca-Cola et Pepsi semblent former une paire naturelle. Leurs activités partagent une clientèle, des intrants et de grands cycles de consommation. Sur 5 000 séances, la régression par moindres carrés ordinaires de leurs cours donne aussi $R^2=0.960$. La première version du projet a pris cet ajustement serré pour une preuve de cointégration, puis construit une stratégie de retour à la moyenne.

Le test formel raconte une autre histoire. Sur l'échantillon d'estimation figé, le test d'Engle-Granger donne une p-valeur de 0.225. Au seuil habituel de 5 %, le résidu ne permet pas de rejeter la présence d'une racine unitaire. Le backtest historique corrigé garde une valeur diagnostique, mais il ne valide pas une stratégie de cointégration exploitable.

J'ai reconstruit l'analyse autour de cette distinction. La nouvelle version fige la régression avant la période de test et normalise chaque résidu avec des données retardées. Elle dimensionne les positions avec le même ratio de couverture que le signal, déduit les frais de négociation et de portage, puis valorise le compte chaque jour. Le résultat est difficile à défendre. 13 opérations clôturées perdent 34 869 \$ avant coûts et 46 228 \$ après coûts. Le capital passe de 100 000 \$ à 53 772 \$.

## Ce que suppose la cointégration

Notons $P^{KO}_t$ le cours de clôture ajusté de Coca-Cola, en dollars américains par action, à la séance $t$. Notons $P^{PEP}_t$ le cours ajusté de Pepsi dans les mêmes unités. La régression d'estimation est

$$
P^{KO}_t = \alpha + \beta P^{PEP}_t + \varepsilon_t,
$$

où $\alpha$ est une constante en dollars américains, $\beta$ le nombre d'actions PEP couvertes pour une action KO et $\varepsilon_t$ le résidu en dollars par action KO. En isolant le résidu, on obtient la combinaison linéaire censée revenir vers sa moyenne :

$$
\varepsilon_t=P^{KO}_t-\alpha-\beta P^{PEP}_t.
$$

Les valeurs estimées sont $\alpha=4.573$ et $\beta=0.3345$. La constante déplace le niveau du résidu, sans modifier le profit et perte d'une position autofinancée puisque $\Delta\alpha=0$.

Un $R^2$ élevé indique seulement que les deux niveaux de prix ont évolué ensemble dans l'échantillon d'estimation. La cointégration exige que $\varepsilon_t$ soit stationnaire, c'est-à-dire que sa loi de probabilité ne continue pas à dériver dans le temps. Un diagnostic courant repose sur la régression du test augmenté de Dickey-Fuller (ADF) :

$$
\Delta\varepsilon_t = \rho\varepsilon_{t-1} + \sum_{i=1}^{p}\gamma_i\Delta\varepsilon_{t-i}+u_t,
$$

où $\Delta\varepsilon_t=\varepsilon_t-\varepsilon_{t-1}$ est la variation journalière du résidu, $p$ le nombre de variations retardées, $\gamma_i$ des coefficients auxiliaires et $u_t$ une erreur imprévisible. L'hypothèse nulle est $\rho=0$, soit une racine unitaire. L'hypothèse stationnaire est $\rho<0$.

Le test ADF ordinaire donne une statistique de -2.630 et une p-valeur de 0.087. Comme le résidu a été estimé au lieu d'être observé, le test d'Engle-Granger applique la loi de MacKinnon appropriée. Sa statistique vaut -2.631 et sa p-valeur 0.225. Aucun des deux tests ne rejette l'hypothèse de racine unitaire à 5 %.

| Diagnostic d'estimation | Valeur | Décision à 5 % |
|---|---:|---|
| $R^2$ de la régression des prix | 0.960 | Ce n'est pas un test de stationnarité |
| P-valeur ADF du résidu | 0.087 | Ne pas rejeter la racine unitaire |
| P-valeur d'Engle-Granger | 0.225 | Ne pas rejeter l'absence de cointégration |

Le code signale ce prérequis manquant au lieu de le masquer :

```python
adf_statistic, adf_pvalue, *_ = adfuller(residual, regression="c", autolag="AIC")
eg_statistic, eg_pvalue, _ = coint(y, x, trend="c", autolag="aic")
```

Le second appel fournit le test formel de cointégration fondé sur les résidus. Le premier reste utile, car il expose directement le test autorégressif sous-jacent.

## Un signal causal

Soit $L=60$ la longueur de la fenêtre mobile. La moyenne disponible à la clôture $t$ n'utilise que les résidus connus jusqu'à $t-1$ :

$$
\bar\varepsilon_{t,L}=\frac{1}{L}\sum_{j=1}^{L}\varepsilon_{t-j}.
$$

Son écart-type empirique vaut

$$
s_{t,L}=\sqrt{\frac{1}{L-1}\sum_{j=1}^{L}
(\varepsilon_{t-j}-\bar\varepsilon_{t,L})^2}.
$$

Le signal est donc

$$
z_t=\frac{\varepsilon_t-\bar\varepsilon_{t,L}}{s_{t,L}}.
$$

Le décalage d'une journée compte. Si le résidu courant entrait dans sa propre moyenne et son propre écart-type, le seuil s'adapterait en partie à l'observation qui déclenche l'ordre. L'implémentation rend ce calendrier explicite :

```python
residual = prices["KO"] - fit.alpha_usd - fit.beta * prices["PEP"]
lagged = residual.shift(1)
rolling_mean = lagged.rolling(rolling_window).mean()
rolling_std = lagged.rolling(rolling_window).std(ddof=1)
z_score = (residual - rolling_mean) / rolling_std
```

Un signal observé à la clôture $t$ fixe les positions après cette clôture. Ces positions gagnent ou perdent sur les variations de prix entre $t$ et $t+1$. Aucune position ne reçoit un mouvement antérieur à l'existence de son signal.

La stratégie achète le résidu pour $-2.5<z_t\leq-1.5$ et le vend pour $1.5\leq z_t<2.5$. Elle clôture lorsque $|z_t|\leq0.2$, déclenche son stop lorsque $|z_t|\geq2.5$ et liquide toute position restante à la fin de l'échantillon. Lorsqu'elle est à plat, elle n'ouvre pas une position déjà au-delà du seuil de stop.

![Résidu fixe de KO et PEP avec bande d'entrée retardée](images/01_spread_regime_shift.png)

La hausse du résidu après 2023 ne se résume pas à quelques franchissements de seuil. Son niveau s'est déplacé. Un z-score mobile peut normaliser cette dérive, mais cette normalisation ne rend pas stationnaire une relation qui ne l'est pas.

## Faire correspondre les positions à l'équation

L'ancien portefeuille utilisait des jambes presque égales en dollars alors que le signal était $P^{KO}_t-\beta P^{PEP}_t$. Il s'agissait de deux portefeuilles différents. Les positions corrigées reproduisent le résidu estimé.

Notons $s_t\in\{-1,0,1\}$ la direction vendeuse, neutre ou acheteuse du résidu. Soit $q_t>0$ le nombre de base d'actions KO. Les positions après la clôture $t$ sont

$$
q^{KO}_t=s_tq_t,
$$

$$
q^{PEP}_t=-s_t\beta q_t.
$$

Leur profit et perte brut sur une journée est

$$
\Pi^{gross}_{t+1}=q^{KO}_t\Delta P^{KO}_{t+1}
+q^{PEP}_t\Delta P^{PEP}_{t+1}.
$$

En remplaçant les positions, on obtient

$$
\Pi^{gross}_{t+1}=s_tq_t
(\Delta P^{KO}_{t+1}-\beta\Delta P^{PEP}_{t+1})
=s_tq_t\Delta\varepsilon_{t+1}.
$$

Le profit et perte négocié correspond maintenant exactement à la variation du résidu modélisé, multipliée par $s_tq_t$. Le signe de la couverture est sans ambiguïté : lorsque $\beta>0$, acheter le résidu revient à acheter KO et à vendre $\beta$ action PEP pour chaque action KO.

À chaque entrée, l'exposition brute cible vaut $G=2C_0$, avec un capital initial $C_0=\$100{,}000$. L'échelle est

$$
q_t=\frac{G}{P^{KO}_t+|\beta|P^{PEP}_t}.
$$

Cette formule donne une exposition brute de 200 % tout en respectant le ratio de la régression. Elle ne garantit ni la neutralité au bêta du marché, ni la neutralité sectorielle, ni la neutralité en dollars. Ces contraintes demanderaient une construction différente.

## Coûts et valorisation quotidienne

Le backtest facture 5 points de base (pbs) par dollar de volume dans un sens. Un point de base vaut 0,01 %, donc 5 pbs valent 0,05 %. Si $c=5/10{,}000$ et si $\Delta q^i_t$ est la variation du nombre d'actions de l'actif $i$, le coût de transaction est

$$
C^{trade}_t=c\sum_i|\Delta q^i_t|P^i_t.
$$

La valeur de marché vendue à découvert supporte un coût d'emprunt annuel de 1 %. La valeur acheteuse supporte un coût de financement annuel de 5 %. Avec $252$ séances par an,

$$
C^{carry}_t=\frac{0.01\,V^{short}_{t-1}+0.05\,V^{long}_{t-1}}{252},
$$

où $V^{short}_{t-1}$ et $V^{long}_{t-1}$ sont des valeurs de marché positives à la clôture précédente. Ces hypothèses restent simplifiées. Les conditions du prime broker, les dividendes dus sur les titres vendus, la disponibilité de l'emprunt, le bid-ask spread et l'impact de marché peuvent modifier la facture.

Le profit et perte net journalier est

$$
\Pi^{net}_t=\Pi^{gross}_t-C^{trade}_t-C^{carry}_t,
$$

et les capitaux propres valorisés chaque jour suivent

$$
E_t=E_{t-1}+\Pi^{net}_t.
$$

Cette comptabilité enregistre chaque jour les gains et pertes des positions ouvertes. L'ancienne courbe, mise à jour seulement à la clôture d'une opération, ne pouvait mesurer le chemin entre deux sorties. Elle ne convenait donc ni au calcul du drawdown ni à l'analyse de marge.

## Résultat corrigé

Le test couvre 494 clôtures quotidiennes, du 11 octobre 2023 au 30 septembre 2025. Tous les coefficients de la régression sont figés à partir des 5 000 observations précédentes.

| Mesure | Valeur corrigée |
|---|---:|
| Opérations clôturées | 13 |
| Opérations rentables | 30.8% |
| Profit et perte brut | -\$34,869 |
| Coûts de transaction | \$2,613 |
| Coûts d'emprunt des ventes | \$1,580 |
| Coûts de financement des achats | \$7,167 |
| Coûts totaux | \$11,359 |
| Profit et perte net | -\$46,228 |
| Rendement total | -46.23% |
| Ratio de Sharpe journalier annualisé | -1.77 |
| Drawdown quotidien maximal | -47.31% |

Le ratio de Sharpe annualisé est la moyenne des rendements nets journaliers divisée par leur écart-type empirique, puis multipliée par $\sqrt{252}$. Aucun taux sans risque n'est retranché, car le coût de financement figure déjà dans le profit et perte journalier.

![Capitaux propres bruts et nets quotidiens avec drawdown](images/03_backtest_equity.png)

Les coûts expliquent 11 359 \$ de perte, mais ils ne sont pas la cause initiale de l'échec. Le profit et perte brut était déjà de -34 869 \$. Le financement domine le modèle de coûts, car la stratégie conserve longtemps une exposition brute proche de 200 %.

La version corrigée clôture 13 opérations contre 21 auparavant. Trois changements expliquent l'écart : les positions suivent désormais le $\beta$ estimé, la règle d'entrée refuse d'ouvrir au-delà du stop et un seul automate causal gère les positions au lieu d'une comptabilité limitée aux opérations achevées.

## Une relation instable en plus d'être non stationnaire

La réestimation par période ne fait pas partie de la règle de trading. Elle sert uniquement au diagnostic après le test.

![Stabilité de la régression selon les échantillons](images/02_parameter_drift.png)

Les trois panneaux concordent. La pente estimée n'a pas persisté, le pouvoir explicatif a fortement baissé et le résidu est devenu beaucoup plus volatil pendant le test.

| Échantillon | $\beta$ | $R^2$ | Volatilité du résidu |
|---|---:|---:|---:|
| Estimation sur 5 000 jours | 0.335 | 0.960 | \$2.72 |
| Deux années précédentes | 0.198 | 0.436 | \$2.14 |
| Période de backtest | -0.216 | 0.197 | \$5.09 |

Le ratio de couverture change de signe pendant le test, la qualité de l'ajustement s'effondre et la volatilité du résidu est presque deux fois supérieure à celle du long échantillon d'estimation. Ce tableau emploie les données futures de la période de test uniquement pour le diagnostic. Réinjecter ces estimations dans les opérations antérieures constituerait un biais d'anticipation.

## Ce que montre réellement le résultat

L'étude montre que la spécification KO-PEP initiale ne satisfait pas son hypothèse statistique et perd de l'argent avec une comptabilité historique cohérente. Elle ne prouve pas que KO et PEP ne peuvent jamais soutenir une opération de valeur relative. Une autre spécification pourrait employer les logarithmes des prix, une fenêtre d'estimation plus courte, des fondamentaux, une couverture des facteurs de marché et de secteur ou un coefficient variable dans le temps. Chaque variante crée une nouvelle hypothèse qui exige un échantillon de test intact.

Les clôtures ajustées restent aussi une approximation imparfaite de l'exécution. Elles intègrent les ajustements de splits et de dividendes dans l'historique, alors qu'une vente à découvert réelle paie les dividendes en espèces et se négocie au prix de marché non ajusté. Un backtest destiné à la production devrait employer des opérations sur titres connues à chaque date, des cours acheteur et vendeur exécutables, la disponibilité de l'emprunt et le modèle de financement du courtier.

Je m'arrêterais à l'échec du test d'Engle-Granger. Le backtest diagnostique reste dans le projet parce qu'il chiffre la décision d'ignorer ce résultat. Le $R^2$ élevé était bien réel. Il répondait à la mauvaise question.

## Références

- Robert F. Engle et Clive W. J. Granger, [« Co-integration and Error Correction: Representation, Estimation, and Testing »](https://doi.org/10.2307/1913236), *Econometrica*, 1987.
- David A. Dickey et Wayne A. Fuller, [« Distribution of the Estimators for Autoregressive Time Series With a Unit Root »](https://doi.org/10.1080/01621459.1979.10482531), *Journal of the American Statistical Association*, 1979.
- James G. MacKinnon, [« Critical Values for Cointegration Tests »](http://qed.econ.queensu.ca/working_papers/papers/qed_wp_1227.pdf), document de travail 1227 du département d'économie de Queen's, 2010.
- Evan Gatev, William N. Goetzmann et K. Geert Rouwenhorst, [« Pairs Trading: Performance of a Relative-Value Arbitrage Rule »](https://doi.org/10.1093/rfs/hhj020), *Review of Financial Studies*, 2006.
- Développeurs de statsmodels, [documentation du test d'Engle-Granger `coint`](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html), interface de la version 0.14.6 employée par ce projet.
