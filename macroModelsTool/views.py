# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pandas as pd
import os

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse
from django.http import HttpResponseRedirect
import statsmodels.api as sm
import statsmodels.formula.api as smf
from .forms import UploadFileForm
import pymysql
from sqlalchemy import create_engine
import pandas as pd
import urllib
from django.http import JsonResponse
import math
import pandas as pd
import os
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import threading
import numpy as np
import threading
import multiprocessing
from multiprocessing import Pool
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
import psycopg2 
import io
from sqlalchemy import event

# To let long strings be represented
pd.set_option("display.max_colwidth", 10000)

num_partitions = 5
num_cores = multiprocessing.cpu_count()
#schema = "macromodelschema."
schema = ""

def loginAccess(request):
    if request.method == 'POST':
        print("Checking user")
        usernameInput = request.POST.get("username",None)
        passwordInput = request.POST.get("password",None)
        print("%s:%s" %(usernameInput, passwordInput))
        user = authenticate(username=usernameInput, password=passwordInput)
        if user is not None:
            # A backend authenticated the credentials
            print("Authenticating credentials")
            print(user)
            login(request, user)
            return redirect('/portal')
        else:
            # No backend authenticated the credentials
            print("No Authenticating credentials")
    template = loader.get_template('login.html')
    return HttpResponse(template.render({},request))

def parallelize_dataframe(df, func):
    parts = np.array_split(df, num_partitions)
    pool = Pool(num_cores)
    df = pd.concat(pool.map(func, parts))
    pool.close()
    pool.join()
    return df

class Persistencia:
    def __init__(self,connection=None):
        self.con = connection
        self.loadVarsOptions()
        self.availablePortfolios()
        self.loadScenarios()

    def loadVarsOptions(self):
        print("Loading Options")
        querySQLServer = "select distinct [First Group], [Second Group], [Third Group], Portfolio from tablaModelos"
        queryPostgreSQL = 'select distinct `First Group`, `Second Group`, `Third Group`, Portfolio from %stablaModelos' %(schema)
        output1 = pd.read_sql(queryPostgreSQL,con)
        print(output1)
        if output1.dropna(subset=['Portfolio']).size == 0:
            print("No models obtained")
            self.options1 = []
            self.options2 = []
            self.options3 = []
            self.optionsPortfolio = []
            return None
        self.options1 = output1[["First Group"]].values
        self.options1 = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in self.options1]))
        self.options1.sort()
        self.options2 = output1[["Second Group"]].values
        self.options2 = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in self.options2]))
        self.options2.sort()
        self.options3 = output1[["Third Group"]].values
        self.options3 = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in self.options3]))
        self.options3.sort()
        self.optionsPortfolio = output1[["Portfolio"]].values
        self.optionsPortfolio = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in self.optionsPortfolio]))
        self.optionsPortfolio.sort()

    def getOptions1(self):
        return self.options1
    def getOptions2(self):
        return self.options2
    def getOptions3(self):
        return self.options3
    '''We are trying to obtain into a class all the needed information for queries/time consuming purposes'''
    def availablePortfolios(self):
        output1 = pd.read_sql("select masterkey from %stablaOpciones order by masterkey" %(schema),con)
        self.portfolios = list(output1["masterkey"].values)
        # update [MIR_WS].[dbo].[tablaOpciones]
        # set masterKey = CONCAT([Portfolio], [Parameter], [Transformation], [Differences], ' AR', [AR])
    def getPortfoliosSatus(self):
        self.availablePortfolios()
        output1 = pd.read_sql("select masterkey, CONCAT(currentprocessed,'/',totaloptions,' ',status) as status from %stablaOpciones order by masterkey" %(schema),con)
        portfoliosStatus = list(output1["status"].values)
        portfoliosKeys = list(output1["masterkey"].values)
        return zip(portfoliosKeys,portfoliosStatus)

    def getPortfolios(self):
        #print self.portfolios
        return self.portfolios

    def loadScenarios(self):
        self.scenarios = {}
        self.scenarios["Historic"] = pd.read_excel('PD Data.xlsx', index_col=0, sheet_name="Vars")
        self.scenarios["Base1"] = pd.read_excel('Base1 Data.xlsx', index_col=0, sheet_name="Vars")
        self.scenarios["Base"] = pd.read_excel('Base Data.xlsx', index_col=0, sheet_name="Vars")
        self.scenarios["Base3"] = pd.read_excel('Base3 Data.xlsx', index_col=0, sheet_name="Vars")

    def getScenario(self,scenario=""):
        return self.scenarios[scenario]

#params = urllib.quote_plus('DRIVER={SQL Server};SERVER=localhost;DATABASE=MIR_WS;UID=sa;PWD=Cocoliso0)')
#engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
#engine = create_engine('postgresql://bbomylezseqnuw:01a5f33037351e96dc0faca6a674e69042dd1a765d29b7b770063663eac85ebe@ec2-184-72-237-95.compute-1.amazonaws.com:5432/d6setjiqb9p7kn')
pymysql.converters.encoders[np.float64] = pymysql.converters.escape_float
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)
engine = create_engine('mysql+pymysql://epz3ofwjth0uo2nj:zmxob5delcmghi3g@j1r4n2ztuwm0bhh5.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/rnqd4v5frbs2v9rn')
con = engine.connect()
mainPersistence = Persistencia(connection=con)

def index(request):
    #print(os.listdir('.'))
    # datos = pd.read_excel('PD Data.xlsx', index_col=0)
    # datos_cleaned = datos.dropna(thresh=1)
    # print(smf.ols(formula="LGD_logit ~ GDPR_logdifQ_m1 + BBBSpread_p1 + HPI_logdifQ_p2",data=datos).fit())
    # datillos = datos.to_html()
    # template = loader.get_template('list.html')
    # return HttpResponse(template.render({}, request))
    return portal(request)
	
@login_required(login_url='/login')
def portal(request):
    return portfoliosModels(request)
	
@login_required(login_url='/login')
def dependentVariables(request):
    documentos = os.listdir('.')
    template = loader.get_template('dependentVariablesTable.html')
    print(documentos)
    existsPdExcel = ("PD Data.xlsx" in documentos)
    existsLGDExcel = ("LGD Data.xlsx" in documentos)
    return HttpResponse(template.render({'existsPdExcel':existsPdExcel,'existsLGDExcel':existsLGDExcel},request))
	
@login_required(login_url='/login')
def independentVariables(request):
    documentos = os.listdir('.')
    template = loader.get_template('independentVariablesTable.html')
    print(documentos)
    existsBaseExcel = ("Base Data.xlsx" in documentos)
    existsBase1Excel = ("Base1 Data.xlsx" in documentos)
    existsBase2Excel = ("Base2 Data.xlsx" in documentos)
    existsBase3Excel = ("Base3 Data.xlsx" in documentos)
    existsSASExcel = ("SAS Data.xlsx" in documentos)
    return HttpResponse(template.render({'existsBaseExcel':existsBaseExcel,
                                        'existsBase1Excel':existsBase1Excel,
                                        'existsBase2Excel':existsBase2Excel,
                                        'existsBase3Excel':existsBase3Excel,
                                        'existsSASExcel':existsSASExcel},
                        request))

@login_required(login_url='/login')
def downloadPDData(request):
    with open('PD Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=PD Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadLGDData(request):
    with open('LGD Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=LGD Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBaseData(request):
    with open('Base Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBase1Data(request):
    with open('Base1 Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base1 (Best) Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBase2Data(request):
    with open('Base2 Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base2 (Pseudo-Base) Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBase3Data(request):
    with open('Base3 Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base3 (Worst) Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadSASData(request):
    with open('SAS Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=SAS (Severely Adverse) Data.xlsx'
        return response
    portal(request)
	
@login_required(login_url='/login')
def uploadPDfile(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["PDDependent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('PD Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['PDDependent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
	return HttpResponseRedirect('dependent')

@login_required(login_url='/login')
def uploadLGDfile(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["LGDDependent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('LGD Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['LGDDependent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('dependent')

@login_required(login_url='/login')
def uploadBasefile(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["BaseIndependent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('Base Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['BaseIndependent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('independent')

@login_required(login_url='/login')
def uploadBase1file(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["Base1Independent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('Base1 Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['Base1Independent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('independent')

@login_required(login_url='/login')
def uploadBase2file(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["Base2Independent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('Base2 Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['Base2Independent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('independent')

@login_required(login_url='/login')
def uploadBase3file(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["Base3Independent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('Base3 Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['Base3Independent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('independent')
    
@login_required(login_url='/login')
def uploadSASfile(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["SASIndependent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('SAS Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['SASIndependent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('independent')
	
@login_required(login_url='/login')
def portfoliosModels(request):
    salida = pd.read_sql("select * from %stablaOpciones order by Portfolio, Parameter, Transformation, Differences, AR" %(schema),con)
    template = loader.get_template('portfoliosOptions.html')
    return HttpResponse(template.render({'data':salida[["Portfolio","Parameter","Transformation","Differences","AR"]].to_html()},request))
	
@login_required(login_url='/login')
def findModel(request):
    salida = pd.read_sql('select distinct `First Group`, `Second Group`, `Third Group` from %stablaModelos' %(schema),con)
    template = loader.get_template('portfoliosOptions.html')
    return HttpResponse(template.render({'data':salida.to_html(),'options1':mainPersistence.getOptions1(),
                                                                'options2':mainPersistence.getOptions2(),
                                                                'options3':mainPersistence.getOptions3(),
                                                                'portfolios':mainPersistence.getPortfolios(),'findModelEnabled':True},request))

@login_required(login_url='/login')
def refreshTable(request):
    group1 = request.GET.get('group1', None)
    group2 = request.GET.get('group2', None)
    group3 = request.GET.get('group3', None)
    filters = []
    if group1 != "Group 1":
        if group1 == "None":
            filters.append('`First Group` is null')
        else:
            filters.append("`First Group` = '" + group1 + "'")
    if group2 != "Group 2":
        if group2 == "None":
            filters.append('`Second Group` is null')
        else:
            filters.append("`Second Group` = '" + group2 + "'")
    if group3 != "Group 3":
        if group3 == "None":
            filters.append('`Third Group` is null')
        else:
            filters.append("`Third Group` = '" + group3 + "'")
    whereClause = " and ".join(filters)
    if whereClause != "":
        whereClause = " where " + whereClause
    query = "select coalesce([First Group],'None') as [First Group],\
                            lag_1Ini, lag_1Fin, coalesce([Second Group],'None') as [Second Group],\
                            lag_2Ini, lag_2Fin,\
                         coalesce([Third Group],'None') as [Third Group], lag_3Ini, lag_3Fin from tablaModelos"+whereClause+" order by \
                [First Group], [Second Group], [Third Group], lag_1Ini, lag_1Fin, lag_2Ini, lag_2Fin, lag_3Ini, lag_3Fin"
    # Change due to lack of RAM Memory in demo server
    mysqlquery = "select coalesce(`First Group`,'None') as `First Group`,\
                            lag_1Ini, lag_1Fin, coalesce(`Second Group`,'None') as `Second Group`,\
                            lag_2Ini, lag_2Fin,\
                         coalesce(`Third Group`,'None') as `Third Group`, lag_3Ini, lag_3Fin from tablaModelos"+whereClause+" order by \
                lag_1Ini, lag_1Fin, lag_2Ini, lag_2Fin, lag_3Ini, lag_3Fin"
    # `First Group`, `Second Group`, `Third Group`,
    print(mysqlquery)
    salida = pd.read_sql(mysqlquery,con)
    salida['index1'] = salida.index
    salida['index1'] = salida['index1'].apply(str)
    salida['Detail'] = "<a href='#'><i class='fas fa-chart-line' firstGroup='"+salida["First Group"]+"'\
                secondGroup='"+salida["Second Group"]+"' ThirdGroup='"+salida["Third Group"]+"'\
                lag_1Ini='"+salida["lag_1Ini"].apply(str)+"' lag_1Fin='"+salida["lag_1Fin"].apply(str)+"'\
                lag_2Ini='"+salida["lag_2Ini"].apply(str)+"' lag_2Fin='"+salida["lag_2Fin"].apply(str)+"'\
                lag_3Ini='"+salida["lag_3Ini"].apply(str)+"' lag_3Fin='"+salida["lag_3Fin"].apply(str)+"'\
                onclick='chartModel(this)'> </i></a>"
    salida.drop(['index1'],axis=1)
# print(salida['Second Group'])

    return JsonResponse({'data':salida.to_html(escape=False, index=False), 'datajson':salida.to_json()})


@login_required(login_url='/login')
def execution(request):
    
    return render(request, 'execution.html', {'portfolios':mainPersistence.getPortfoliosSatus()})

@login_required(login_url='/login')
def executePortfolio(request):
    portfolioKey = request.GET.get("portfolio",None)
    print("Portfolio to queue %s" %(portfolioKey))
    p = threading.Thread(target=executePortfolioConcurrent, args=(portfolioKey,))
    print("Starting Thread")
    p.start()
    return JsonResponse({"status":"Executing"})

def executePortfolioConcurrent(portfolioKey):
    print("Portfolio selected = %s" %(portfolioKey))
    output1 = pd.read_sql("select * from %stablaOpciones where masterkey='%s'" %(schema, portfolioKey),con)
    infoPortfolio = output1.iloc[0]
    portfolio = str(infoPortfolio["Portfolio"]).strip()
    parameter = infoPortfolio["Parameter"]
    transformation = infoPortfolio["Transformation"]
    datosBase = mainPersistence.getScenario("Base")
    listado = [["GDPR",1],
               ["Unemployment",1],
                ["HPI",3],
                ["OilPrices",3],
                ["Sovereign1yA",2],
                ["Sovereign10yA",2],
                ["BBBSpread",2],
                ["CRE",3],
                ["PD_logit",4]]

    grupos = ["Listado de grupos",set([None]),set([None]),set([None]),set([None])]
    eliminar = ["_m1","_m2","_m3","_m4","_p1","_p2","_p3","_p4"]


    permitido = ["GDPR_logdifa","BBBSpread","CRE_logdifa"]

    for k in datosBase.columns:
        for j in listado:
            if (j[0] in k):
                for i in eliminar:
                    k = k.replace(i,"")
                if k in permitido:
                    grupos[j[1]].add(k)
 
    newDf = pd.DataFrame(mainPersistence.getScenario("Historic")[portfolio])
    newDf["PD_Logit"] = newDf[portfolio].apply(lambda x: math.log(x/(1-x)))

    datosBase["PD_Logit"] = newDf["PD_Logit"]
    datosBase["PD"] = newDf[portfolio]

    dfg1 = pd.DataFrame({'key':[1 for k in range(len(grupos[1]))],'key1':[1 for k in range(len(grupos[1]))],"First Group":list(grupos[1])})
    dfg1.loc[dfg1["First Group"].isnull(),["key1"]] = 0
    dfg2 = pd.DataFrame({'key':[1 for k in range(len(grupos[2]))],'key2':[1 for k in range(len(grupos[2]))],"Second Group":list(grupos[2])})
    dfg2.loc[dfg2["Second Group"].isnull(),["key2"]] = 0
    dfg3 = pd.DataFrame({'key':[1 for k in range(len(grupos[3]))],'key3':[1 for k in range(len(grupos[3]))],"Third Group":list(grupos[3])})
    dfg3.loc[dfg3["Third Group"].isnull(),["key3"]] = 0
    Aux1 = pd.merge(pd.merge(dfg1,dfg2,on='key'),dfg3, on='key')
    dfAR = pd.DataFrame({'key':[1 for k in range(len(grupos[4]))],'key4':[1 for k in range(len(grupos[4]))],"AR Group":list(grupos[4])})
    dfAR.loc[dfAR["AR Group"].isnull(),["key4"]] = 0
    Aux1 = pd.merge(Aux1,dfAR, on='key')

    dfg1Ini = pd.DataFrame({'key1':[1 for k in range(5)]+[0],'lag_1Ini':[-2,-1,0,1,2,0]})
    dfg1Fin = pd.DataFrame({'key1':[1 for k in range(5)]+[0],'lag_1Fin':[-2,-1,0,1,2,0]})
    print('First group lagged defined')
    dfg2Ini = pd.DataFrame({'key2':[1 for k in range(5)]+[0],'lag_2Ini':[-2,-1,0,1,2,0]})
    dfg2Fin = pd.DataFrame({'key2':[1 for k in range(5)]+[0],'lag_2Fin':[-2,-1,0,1,2,0]})
    print('Second group lagged defined')
    dfg3Ini = pd.DataFrame({'key3':[1 for k in range(5)]+[0],'lag_3Ini':[-2,-1,0,1,2,0]})
    dfg3Fin = pd.DataFrame({'key3':[1 for k in range(5)]+[0],'lag_3Fin':[-2,-1,0,1,2,0]})
    print('Third group lagged defined')
    dfARIni = pd.DataFrame({'key4':[1 for k in range(1)]+[0],'lag_ARIni':[0,0]})
    dfARFin = pd.DataFrame({'key4':[1 for k in range(1)]+[0],'lag_ARFin':[0,0]})
    print('AR group merged')
    #Estamos intentando mergear para cosneguir las combinaciones de los modelos

    Aux1 = pd.merge(Aux1,dfg1Ini,on='key1')
    Aux1 = pd.merge(Aux1,dfg1Fin,on='key1')
    print('First group merged')
    Aux1 = pd.merge(Aux1,dfg2Ini,on='key2')
    Aux1 = pd.merge(Aux1,dfg2Fin,on='key2')
    print('Second group merged')
    Aux1 = pd.merge(Aux1,dfg3Ini,on='key3')
    Aux1 = pd.merge(Aux1,dfg3Fin,on='key3')
    print('Third group merged')
    Aux1 = pd.merge(Aux1,dfARIni,on='key4')
    Aux1 = pd.merge(Aux1,dfARFin,on='key4')
    print('AR group merged')
    Aux1 = Aux1.loc[((Aux1['lag_1Fin'] >= Aux1['lag_1Ini']) | Aux1['First Group'].isnull())
                    & ((Aux1['lag_2Fin'] >= Aux1['lag_2Ini']) | Aux1['Second Group'].isnull())
                   & ((Aux1['lag_3Fin'] >= Aux1['lag_3Ini']) | Aux1['Third Group'].isnull())
                   & ((Aux1['lag_ARFin'] >= Aux1['lag_ARIni']) | Aux1['AR Group'].isnull())]
    numeroVars = 16
    for k in range(0, numeroVars, 1):
        Aux1["Var"+str(k)] = ''
        Aux1["Coef"+str(k)] = ''
    Aux1 = Aux1.reset_index()
    model1 = None
    query = "update %stablaOpciones set currentprocessed=0,  totaloptions=%s where masterkey='%s'" %(schema, str(len(Aux1.index)),portfolioKey)
    con.execute(query)
    print(query)
    def functioncilla(x):
        opciones = []
        if x["First Group"] != None:
            for k in range(x["lag_1Ini"],x["lag_1Fin"]+1,1):
                if k < 0:
                    opciones.append(x["First Group"]+"_m"+str(abs(k)))
                elif k > 0:
                    opciones.append(x["First Group"]+"_p"+str(abs(k)))
                else:
                    opciones.append(x["First Group"])
        if x["Second Group"] != None:       
            for k in range(x["lag_2Ini"],x["lag_2Fin"]+1,1):
                if k < 0:
                    opciones.append(x["Second Group"]+"_m"+str(abs(k)))
                elif k > 0:
                    opciones.append(x["Second Group"]+"_p"+str(abs(k)))
                else:
                    opciones.append(x["Second Group"])
        if x["Third Group"] != None: 
            for k in range(x["lag_3Ini"],x["lag_3Fin"]+1,1):
                if k < 0:
                    opciones.append(x["Third Group"]+"_m"+str(abs(k)))
                elif k > 0:
                    opciones.append(x["Third Group"]+"_p"+str(abs(k)))
                else:
                    opciones.append(x["Third Group"])
        if x["AR Group"] != None: 
            for k in range(x["lag_ARIni"],x["lag_ARFin"]+1,1):
                if k < 0:
                    opciones.append(x["AR Group"]+"_m"+str(abs(k)))
                elif k > 0:
                    opciones.append(x["AR Group"]+"_p"+str(abs(k)))
                else:
                    opciones.append(x["AR Group"])

        variables = ['PD_Logit'] + opciones
        #print(opciones)
        cleaned_data = datosBase.loc[:,variables].dropna()
        #print(cleaned_data)
        try:
            #cleaned_data = cleaned_data.drop('2008-2Q')
            #cleaned_data = cleaned_data.drop('2008-1Q')
            None
        except:
            None
        #print(opciones)
        if len(opciones) == 0:
            return x
        stringVars = variables[0] + " ~ " + " + ".join(opciones)
        model1 = smf.ols(formula=stringVars,data=cleaned_data).fit()
        x["Var0"] = "Intercept"
        x["Coef0"] = model1.params["Intercept"]
        for k in range(1, len(opciones)+1, 1):
            x["Var"+str(k)] = opciones[k-1]
            x["Coef"+str(k)] = model1.params[opciones[k-1]]
        x["AIC"] = model1.aic
        x["F-pvalue"] = model1.f_pvalue
        x["R2"] = model1.rsquared
        x["MSE"] = model1.mse_model
        x["Transformation"] = "Logit"
        x["Portfolio"] = portfolio
        x["`context`"] = "IFRS9 2019"

        print("%s - %s" %(portfolioKey,x.name))
        print("Starting db copy")
        #print(pd.DataFrame(x).to_sql(con=con, name='%stablaModelos' %(schema), if_exists='append'))
        if int(x.name)%999 == 0:
            print("%s Progress: %s" %(portfolio,str(x.name)))
            con.execute("update %stablaOpciones set currentprocessed=%s where masterkey='%s'" %(schema,str(int(x.name)+1),portfolioKey))

        return x

    #def applyFunctioncilla(dataAux):
    #    return pd.DataFrame(dataAux.apply(functioncilla, axis=1))

    #Salida = parallelize_dataframe(Aux1, applyFunctioncilla)
    salida = pd.DataFrame(Aux1[Aux1.index < 50].apply(functioncilla, axis=1))
    #model1 = functioncilla(Aux1.iloc[0])
    query = "update %stablaOpciones set currentprocessed=%s,  totaloptions=%s where masterkey='%s'" %(schema, str(len(Aux1.index)),str(len(Aux1.index)),portfolioKey)
    con.execute(query)
    #query = "delete from %stablaModelos where masterkey ='%s'" %(schema, portfolioKey)
    #con.execute(query)
    # Only for PostgreSQL

    print(salida.to_sql(con=con, name='tablaModelos', if_exists='replace'))
    del Aux1
    mainPersistence.loadVarsOptions()

def predict(coefs=None, years=50, transformation="", historic=None, scenarioData=None):
    output = []
    labels = []
    if (coefs is None or historic is None or scenarioData is None):
        return None
    print("Running Forecasting")
    scenarioData["Quarter"] = scenarioData.index
    for index, row in scenarioData.iterrows():
        #print(index)
        y = 0
        maxVars = 18
        for k in range(0,maxVars):
            varName = coefs.iloc[0]["Var"+str(k)]
            if varName=="":
                break
            coefficient = float(coefs.iloc[0]["Coef"+str(k)])
            if varName=="Intercept":
                y=y+coefficient
                continue
            y = y+(coefficient*float(scenarioData.loc[index,coefs.iloc[0]["Var"+str(k)]]))
        #print(y)
        if transformation=="Logit":
            y=math.exp(y)/(1+math.exp(y))
            #print(y)
        if math.isnan(y) or len(output)>90:
            continue
            #output.append("")
        else:
            labels.append(row["Quarter"])
            output.append(round(y*100,2))
    return output, labels

def getStatistics(info):
    newDf = pd.DataFrame({'Statistic':['AIC','F-pvalue',"R2","MSE"],
                        'Value':[info["AIC"],info["F-pvalue"],info["R2"],info["MSE"]]})
    return newDf.to_html()
def getCoefficients(info):
    descriptions = []
    values = []

    for k in range(16):
        var = info["Var"+str(k)]
        coef = info["Coef"+str(k)]
        if var == "":
            break
        descriptions.append(var)
        values.append(coef)
    newDf = pd.DataFrame({'Statistic':descriptions,
                        'Value':values})
    return newDf.to_html()

@login_required(login_url='/login')
def modelProjection(request):

    firstGroup = request.GET.get("firstGroup",None)
    # print(firstGroup)
    secondGroup = request.GET.get("secondGroup",None)
    # print(secondGroup)
    thirdGroup = request.GET.get("thirdGroup",None)
    # print(thirdGroup)
    lag_1Ini = request.GET.get("lag_1Ini",None)
    # print(lag_1Ini)
    lag_1Fin = request.GET.get("lag_1Fin",None)
    # print(lag_1Fin)
    lag_2Ini = request.GET.get("lag_2Ini",None)
    # print(lag_2Ini)
    lag_2Fin = request.GET.get("lag_2Fin",None)
    # print(lag_2Fin)
    lag_3Ini = request.GET.get("lag_3Ini",None)
    # print(lag_3Ini)
    lag_3Fin = request.GET.get("lag_3Fin",None)
    # print(lag_3Fin)

    whereClause = " where coalesce(`First Group`,'None')='%s' and coalesce(`Second Group`,'None')='%s' and coalesce(`Third Group`,'None')='%s' \
                    and lag_1Ini=%s and lag_1Fin=%s \
                    and lag_2Ini=%s and lag_2Fin=%s \
                    and lag_3Ini=%s and lag_3Fin=%s \
                    " %(firstGroup, secondGroup, thirdGroup, lag_1Ini, lag_1Fin, lag_2Ini, lag_2Fin, lag_3Ini,lag_3Fin)
    query = "select * from %stablaModelos" %(schema) +whereClause
    #print(query)
    salida = pd.read_sql(query,con)

    portfolio = "SB - CF&A Secured"
    series = {}
    series["Base"], labels = predict(coefs=salida,transformation="Logit",historic=mainPersistence.getScenario(scenario="Historic"),
            scenarioData=mainPersistence.getScenario(scenario="Base"))
    series["Base1"], labels = predict(coefs=salida,transformation="Logit",historic=mainPersistence.getScenario(scenario="Historic"),
            scenarioData=mainPersistence.getScenario(scenario="Base1"))
    series["Base3"], labels = predict(coefs=salida,transformation="Logit",historic=mainPersistence.getScenario(scenario="Historic"),
            scenarioData=mainPersistence.getScenario(scenario="Base3"))
    series["Historical"] = labels
    #series["Historical"] = list(mainPersistence.getScenario(scenario="Base").index.values)
    #print(list(series["Base"].values))
    return JsonResponse({"Base":series["Base"],
                        "Base1":series["Base1"],
                        "Base3":series["Base3"],
                        "labels":series["Historical"],
                        "statistics":getStatistics(salida.iloc[0]),
                        "coefficients":getCoefficients(salida.iloc[0])})