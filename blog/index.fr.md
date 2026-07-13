---
title: "Quand une paire cointégrée cesse de l'être"
description: "Une étude de pairs trading sur KO et PEP qui semblait prometteuse en simulation, a perdu 34 % en backtest et a révélé le coût d'un ratio de couverture instable."
date: 2026-07-13
image: images/cover-cointegration-regime-break.png
categories: ["Quantitative Research", "Risk Management"]
---

# Quand une paire cointégrée cesse de l'être

Coca-Cola et Pepsi semblent former une paire naturelle. Les deux entreprises vendent des produits comparables, subissent plusieurs des mêmes coûts de production et leurs actions ont souvent évolué ensemble. Cette logique économique suffit à envisager une opération de valeur relative. Elle ne prouve pas que la relation entre les prix reviendra vers sa moyenne.

Ce projet m'a surtout fourni un bon cas d'échec. Une exécution de contrôle de Monte Carlo sur 10 000 trajectoires donnait un taux de réussite de 69,9 %, un profit et perte (P&L) médian de 3 050 \$ et un ratio de Sharpe simulé de 1,05. Le test historique ultérieur aboutit au résultat inverse. Vingt et une opérations clôturées perdent 34 009 \$ avant frais de transaction, faisant passer un compte de 100 000 \$ à environ 65 991 \$.

Le code n'a pas cassé. La relation, elle, a changé.

## De deux prix à un seul spread

Notons $P^{KO}_t$ le cours de clôture ajusté de Coca-Cola au jour de bourse $t$, et $P^{PEP}_t$ celui de Pepsi. Le projet estime la régression linéaire des prix par moindres carrés ordinaires

$$
P^{KO}_t = \alpha + \beta P^{PEP}_t + \varepsilon_t,
$$

où $\alpha$ est l'ordonnée à l'origine, $\beta$ le ratio de couverture et $\varepsilon_t$ le résidu de la régression. Il définit ensuite le spread négocié par

$$
S_t = P^{KO}_t - \beta P^{PEP}_t.
$$

Sur les 5 000 dernières observations précédant le 9 octobre 2023, les données figées du projet donnent $\beta=0.335$ et $R^2=0.960$. Le coefficient de détermination $R^2$ mesure la part de la variation du cours de KO expliquée par la relation estimée.

Ce $R^2$ élevé est séduisant sur un graphique, mais ce n'est pas un test de cointégration. La cointégration exige que le résidu, ou une combinaison linéaire équivalente de prix non stationnaires, soit stationnaire. Le dépôt n'applique ni test augmenté de Dickey-Fuller aux résidus, ni test d'Engle-Granger, ni test de Johansen. Il est donc plus exact de parler d'une *hypothèse de cointégration* fondée sur un ajustement historique marqué.

Cette nuance compte. Deux séries de prix tendancielles peuvent afficher un $R^2$ élevé, puis s'éloigner durablement.

## Transformer le spread en signal

La stratégie compare le spread à une fenêtre mobile de 60 séances. Notons $L=60$ la longueur de cette fenêtre, $\bar S_{t,L}$ la moyenne mobile du spread et $s_{t,L}$ son écart-type mobile. Le z-score vaut

$$
z_t = \frac{S_t-\bar S_{t,L}}{s_{t,L}}.
$$

Le backtest historique entre acheteur sur le spread lorsque $z_t<-1.5$ et vendeur lorsque $z_t>1.5$. La position est fermée près de la moyenne si $|z_t|<0.2$, ou coupée si $|z_t|>2.5$.

La construction des positions pose toutefois un problème. Le signal emploie le $\beta$ estimé, tandis que le portefeuille achète environ 100 000 \$ d'une action et vend environ 100 000 \$ de l'autre. Les jambes sont presque neutres en dollars, mais pas neutres selon le bêta de la régression. Le modèle et les positions réelles portent donc sur deux combinaisons linéaires différentes de KO et PEP. Une mise en production devrait d'abord fixer la définition de l'exposition, puis l'appliquer sans changement au signal, à la simulation, au profit et perte et aux mesures de risque.

## Comment la simulation impose le retour à la moyenne

La simulation part de mouvements browniens géométriques corrélés. Pour l'action $i$, KO ou PEP, la mise à jour journalière est

$$
P_{i,t+1}=P_{i,t}\exp\left[\left(\mu_i-\frac{1}{2}\sigma_i^2\right)\Delta t+\sigma_i\sqrt{\Delta t}\,\epsilon_{i,t}\right].
$$

Ici, $\mu_i$ désigne la dérive quotidienne, $\sigma_i$ la volatilité quotidienne, $\Delta t=1$ séance et $\epsilon_{i,t}$ un choc suivant une loi normale centrée réduite. Une factorisation de Cholesky donne aux chocs de KO et PEP leur corrélation estimée, proche de 0,689.

Le projet ajoute un processus d'Ornstein-Uhlenbeck pour ramener le spread vers une cible récente :

$$
dS_t=\kappa(\theta-S_t)dt+\sigma_S dW_t.
$$

Le paramètre $\kappa$ est la vitesse de retour à la moyenne, $\theta$ le spread cible, $\sigma_S$ la diffusion du spread et $W_t$ un mouvement brownien. La demi-vie supposée est de $h=10$ séances, d'où

$$
\kappa=\frac{\ln 2}{h}=0.0693.
$$

Un détail de l'implémentation est particulièrement soigné. Si $A_t$ représente l'ajustement d'Ornstein-Uhlenbeck sur une journée, le code le répartit entre les deux actions selon

$$
w_{KO}=\frac{1}{1+\beta^2}, \qquad w_{PEP}=\frac{\beta}{1+\beta^2}.
$$

Si ces montants sont appliqués comme des variations additives des prix, le cours de KO reçoit $w_{KO}A_t$ et celui de PEP reçoit $-w_{PEP}A_t$. La variation du spread devient alors

$$
\Delta S_t=w_{KO}A_t-\beta(-w_{PEP}A_t)
=A_t\frac{1+\beta^2}{1+\beta^2}=A_t.
$$

Le code divise toutefois ces deux montants par le cours courant, puis les place dans une mise à jour exponentielle du rendement. L'identité ci-dessus n'est donc exacte qu'au premier ordre lorsque $A_t/P_{i,t}$ est petit, et non pour un pas fini. Voici le bloc essentiel de l'implémentation :

```python
weight_ko = 1 / (1 + beta**2)
weight_pep = beta / (1 + beta**2)

current_spread = ko_prices[:, day] - beta * pep_prices[:, day]
ou_drift = kappa * (spread_mean - current_spread) * dt
ou_diffusion = spread_volatility * np.sqrt(dt) * z[:, 2]
ou_adjustment = ou_drift + ou_diffusion

ko_ou_return = (ou_adjustment * weight_ko) / ko_prices[:, day]
pep_ou_return = -(ou_adjustment * weight_pep) / pep_prices[:, day]
```

La répartition est raisonnable lorsque les ajustements quotidiens restent petits. La question difficile est ailleurs : une demi-vie de dix séances et une cible fixe proche de zéro décrivent-elles les deux années suivantes ? La simulation suppose que oui.

## Le risque à l'intérieur du modèle

Le projet valorise un portefeuille dont l'exposition brute approche 200 % : une jambe longue de 100 000 \$ et une jambe courte de 100 000 \$, pour un capital de 100 000 \$. Notons $L_H$ la perte en dollars à l'horizon $H$, et $q_c(L_H)$ son quantile au niveau de confiance $c$. La valeur à risque et l'Expected Shortfall sont définis par

$$
\operatorname{VaR}_c=q_c(L_H),
$$

$$
\operatorname{ES}_c=\mathbb{E}\left[L_H\mid L_H\geq \operatorname{VaR}_c\right].
$$

À 60 jours, l'exécution de contrôle sur 10 000 trajectoires estime la valeur à risque (VaR) à 95 % à 4 472 \$ et l'Expected Shortfall (ES) à 95 % à 5 788 \$. Autrement dit, 5 % des scénarios simulés perdent plus de 4 472 \$, et la perte moyenne au sein de ces 5 % atteint 5 788 \$.

La même exécution donne des valeurs à risque à 95 % nettement supérieures par rééchantillonnage historique (10 694 \$) et par calcul paramétrique normal (11 095 \$). Cet écart entre méthodes constitue déjà un avertissement : l'estimation de la queue dépend autant du modèle de rendements que du portefeuille.

## Le régime s'est déplacé

Sur les 60 séances précédant l'opération, la moyenne du spread était de 0,004 \$ et son écart-type de 0,769 \$. Ces valeurs déterminent la cible et la diffusion de la simulation. Le graphique applique le ratio de couverture fixe estimé sur 20 ans à l'échantillon quotidien figé jusqu'au 30 septembre 2025.

![Spread KO-PEP à bêta fixe avant et après la date de calibration](images/01_spread_regime_shift.png)

Après la date de calibration, le spread n'oscille plus autour de zéro. Il monte durablement, avec une moyenne de 12,20 \$ et un écart-type de 8,19 \$ pendant le backtest. Cette volatilité vaut 10,6 fois l'estimation de calibration. Le retour vers l'ancienne cible est devenu une mauvaise prévision conditionnelle.

Une nouvelle estimation de la relation par période rend la rupture encore plus nette.

![Ratio de couverture, qualité de la régression et volatilité du spread par période](images/02_parameter_drift.png)

Le ratio de couverture estimé passe de 0,335 sur 20 ans à 0,197 pendant les deux années précédant l'opération, puis devient négatif à -0,216 durant le backtest. Dans le même temps, $R^2$ tombe de 0,960 à 0,197. Un coefficient de long terme stable ne devrait pas se comporter ainsi. Avant même octobre 2023, l'estimation sur deux ans signalait que celle sur 20 ans mélangeait plusieurs régimes.

## Confiance en simulation, perte en historique

La stratégie historique reprend les seuils de z-score sur 60 jours, les quantités fixes et le ratio de couverture historique du projet. Elle clôture 21 opérations entre octobre 2023 et septembre 2025. Six sont gagnantes, soit un taux de réussite de 28,6 %. Le profit et perte total atteint -34 009 \$ avant frais de transaction, coût d'emprunt des titres, dividendes dus sur la jambe courte ou impact de marché. La durée de détention moyenne est de 20,2 jours calendaires.

![Courbe de capital historique après chaque opération clôturée](images/03_backtest_equity.png)

La courbe ne mesure le capital qu'à la clôture d'une opération, comme le fait le projet. Ce n'est pas une valorisation quotidienne au marché. Elle omet donc une partie de l'information nécessaire au calcul du drawdown et du risque de marge. Même avec cette omission favorable, le résultat est mauvais. La pire opération perd 11 490 \$, contre un gain de 3 342 \$ pour la meilleure.

Le tableau sépare volontairement l'échantillon simulé de l'échantillon historique :

| Mesure | Simulation sur 10 000 trajectoires | Backtest historique |
|---|---:|---:|
| Taux de réussite | 69.9% | 28.6% |
| P&L simulé médian / P&L total du backtest | \$3,050 | -\$34,009 |
| Ratio de Sharpe | 1.05 | Non calculé à partir de rendements quotidiens valorisés au marché |
| Opérations clôturées | Opérations simulées dépendantes de la trajectoire | 21 |

La simulation n'est pas « fausse » au regard de ses propres hypothèses. Elle répond à une question plus étroite : que se passe-t-il si les chocs de prix restent corrélés et si une force d'Ornstein-Uhlenbeck continue de ramener l'ancien spread vers l'ancienne cible ? Le backtest indique ce qui s'est produit quand ces deux hypothèses de stabilité ont cessé de tenir.

## Ce que je changerais avant de négocier cette paire

Je commencerais par tester le résidu. Une procédure d'Engle-Granger mobile ou un test augmenté de Dickey-Fuller sur un résidu hors échantillon permettrait de vérifier si la stationnarité est suffisamment étayée pour justifier un modèle de retour à la moyenne. Il faudrait accompagner ce test de contrôles de stabilité sur $\beta$, et non le traiter comme un certificat définitif.

Je séparerais ensuite la sélection du modèle de l'évaluation des opérations. Estimer $\beta$, choisir la fenêtre de 60 jours, fixer les seuils d'entrée et juger la performance sur des données qui se chevauchent crée du biais de sélection et du lookahead, c'est-à-dire l'emploi d'une information qui n'aurait pas été disponible à la date de décision. Une procédure walk-forward estimerait les paramètres sur une fenêtre, les figerait, puis évaluerait la fenêtre suivante.

Les positions devraient aussi correspondre au spread. Si le signal est $P^{KO}-\beta P^{PEP}$, le ratio entre les quantités doit suivre ce même $\beta$, après prise en compte du capital et des contraintes de risque. Des jambes de même montant constituent un autre portefeuille et demandent leur propre modèle de signal.

Enfin, il faut valoriser les positions chaque jour et facturer le coût réel de l'opération. Les commissions sont probablement le poste le moins préoccupant ici. Le bid-ask spread, le coût d'emprunt, les dividendes dus sur la vente à découvert, le financement et les sorties forcées peuvent peser davantage avec une exposition brute de 200 % et des positions détenues plusieurs semaines.

Le résultat le plus instructif du projet n'est pas le ratio de Sharpe simulé. C'est le diagnostic de son échec hors échantillon : un ajustement élevé sur l'ensemble des données cachait un coefficient instable, la simulation imposait le retour à la moyenne qu'elle semblait ensuite observer, et le portefeuille négocié ne correspondait pas exactement au spread modélisé. En pairs trading, la stabilité de la relation fait partie du modèle de risque.
