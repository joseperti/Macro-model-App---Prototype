
import statsmodels.api as sm
import statsmodels.formula.api as smf
import pandas as pd
import os

datos = pd.read_excel('PD Data.xlsx', index_col=0)
datos_cleaned = datos.dropna(thresh=1)
print(smf.ols(formula="LGD_logit ~ GDPR_logdifQ_m1 + BBBSpread_p1 + HPI_logdifQ_p2",data=datos).fit())
datillos = datos.to_html()
