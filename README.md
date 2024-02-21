# CGT - Crypto to Gold Indicator

## Introduction

This project creates a new Technical Analisys indicator that uses the ratio between two prices: Crypto X Gold, then calculates ROC (Rate of Change) for 4 previous weeks over this ratio. 
The number obtained by this formula is then used to create a buy/sell signal to be used in a trading strategy.

* The inspiration for this project is the "Saylor to Schiff Indicator" developed by the trader Michael Silva: https://www.youtube.com/watch?v=zuG9Tjnud9k


## TODO: Create a best way to address the problem with linear interpolation

### (in Portuguese) Problema de interpolação de dados

Devido ao ROC calcular a variação de 4 semanas atras e fechar em uma data, neste caso "W-SUN"(domingo)
existe um problema de consistência de valores quando se converte de roc semanal para roc diário
através de interpolação de dados.

Possivelmente haverá inconsistência nos valores diários históricos para uma semana que ainda não fechou.

Ex:

Digamos que hoje é terça-feira 2023-01-31 e o roc se encontra em 100 (pois p=14 é 100% maior que p=07 4 semans antes 2023-01-08).
Este valor de roc 100 é o projetado para a data de 2023-02-05 BASEADO no preço de terça-feira, porém como a semana
não terminou não é possiveld eterminar o real roc:
```
t   | 2023-01-01| 2023-01-08| 2023-01-15| 2023-01-22| 2023-01-29| 2023-01-31| 2023-02-05|
w   |   -4      |    -3     |   -2      |    -1     |    0      | 1 (going) |    1      |
wd  | sunday    | sunday    | sunday    | sunday    | sunday    |  tuesday  | sunday    |
p   |   10      |   07      |   11      |   09      |   11      |    14     |    ??     |
roc |  NaN      |  NaN      |  NaN      |  NaN      |   10      |   100     |    ??     |
```

O roc só apresenta os valores a cada semana (1 data point/week) a cada domingo, porém, para plotar um gráfico mais "polido" é possível interpolar os dados intermediários, de forma linear. Com isso se reconstroi artificialemnte daodos históricos de valores para o roc.

Podemos obter o roc de ontem, segunda-feira 2023-01-30 interpolando o roc de domingo 2023-01-29 (roc=10) com o roc projetado 2023-02-05, que foi calculado na terça-feira 2023-01-31(roc=100):

O roc de segunda-feira 2023-01-30 seria de 55

```
t   | 2023-01-29| 2023-01-30| 2023-01-31|
w   |    0      | 1 (going) | 1 (going) |
wd  | sunday    |  monday   | tuesday   |
p   |   11      |    ??     |    14     |
roc |   10      |   55      |    100    |
```
Este valor iria parar em um dataframe e registrado para a tomada de decisões. Porém, ao virar o dia e agora sendo quarta-feira  2023-02-01, tanto o valor para a segunda-feira quanto para a terça-feira serão recalculados baseados no valor projetado para o próximo domingo, que efetivamente 'e o roc da quarta-feira:

```
t   | 2023-01-29| 2023-01-30| 2023-01-31|2023-02-01|
w   |    0      | 1 (going) | 1 (going) |1 (going) |
wd  | sunday    |  monday   | tuesday   |wednesday |
p   |   11      |    ??     |    14     |    14    |
roc |   10      |   40      |    70     |    100   |
```
Neste novo cálculo, o roc atual não mudou, continua sendo 100, porém o roc de ontem, terça-feira, que também era 100 agora passa a ser 70. O roc de segunda-feira, que ontem era 55, hoje é 40.