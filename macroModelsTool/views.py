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
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
import psycopg2 
import io
from sqlalchemy import event
import datetime

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

def logoutAccess(request):
    logout(request)
    return redirect('/portal')

class Persistencia:
    def __init__(self,connection=None):
        self.con = connection
        self.loadContexts()
        self.loadVarsOptions()
        self.availablePortfolios()
        self.loadScenarios()

    def loadContexts(self):
        print("Loading Contexts")
        output1 = pd.read_sql("select context_name from %scontextlist order by context_name" %(schema),self.con)
        self.contextList = list(output1["context_name"].values)
        print(self.contextList)

    def getContext(self):
        return self.contextList

    def setContextSession(self, chosenContext, request):
        print("Setting context %s" %(chosenContext))
        if chosenContext in self.contextList:
            request.session["context"] = chosenContext
        return None

    def getContextSession(self, request):
        try:
            return request.session["context"]
        except:
            if len(self.contextList) > 0:
                request.session["context"] = self.contextList[0]
            else:
                request.session["context"] = "Demo"
            return self.getContextSession(request)

    def loadVarsOptions(self):
        print("Loading Options")
        self.options1 = dict()
        self.options2 = dict()
        self.options3 = dict()
        self.optionsPortfolio = dict()
        for c in self.getContext():
            querySQLServer = "select distinct [First Group], [Second Group], [Third Group], Portfolio from tablaModelos"
            queryPostgreSQL = 'select distinct `First Group`, `Second Group`, `Third Group`, Portfolio from %stablaModelos where `context`="%s"' %(schema, c)
            output1 = pd.read_sql(queryPostgreSQL,con)
            print(output1)
            if output1.dropna(subset=['Portfolio']).size == 0:
                print("No models obtained for %s" %(c))
                options_1 = []
                options_2 = []
                options_3 = []
                optionsPortfolio_ = []
            options_1 = output1[["First Group"]].values
            options_1 = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in options_1]))
            #options_1.sort()
            options_2 = output1[["Second Group"]].values
            options_2 = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in options_2]))
            #options_2.sort()
            options_3 = output1[["Third Group"]].values
            options_3 = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in options_3]))
            #options_3.sort()
            optionsPortfolio_ = output1[["Portfolio"]].values
            optionsPortfolio_ = list(set([k[0].encode("ascii") if k[0]!=None else k[0] for k in optionsPortfolio_]))
            #optionsPortfolio_.sort()
            self.options1[c] = options_1
            self.options2[c] = options_2
            self.options3[c] = options_3
            self.optionsPortfolio[c] = optionsPortfolio_

        del options_1
        del options_2
        del options_3
        del optionsPortfolio_
        return None
    def getPortfolios(self, context="", request=None):
        #print self.portfolios
        if request != None:
            context = self.getContextSession(request)
        if context == "":
            context = self.optionsPortfolio.keys()[0]
        return self.optionsPortfolio[context]

    def getOptions1(self, context="", request=None):
        if request != None:
            context = self.getContextSession(request)
        if context == "":
            context = self.options1.keys()[0]
        print(self.options1[context])
        return self.options1[context]
    def getOptions2(self, context="", request=None):
        if request != None:
            context = self.getContextSession(request)
        if context == "":
            context = self.options2.keys()[0]
        return self.options2[context]
    def getOptions3(self, context="", request=None):
        if request != None:
            context = self.getContextSession(request)
        if context == "":
            context = self.options3.keys()[0]
        return self.options3[context]
    '''We are trying to obtain into a class all the needed information for queries/time consuming purposes'''
    def availablePortfolios(self):
        print("Loading available Portfolios")
        output1 = pd.read_sql("select masterkey from %scurrentModels order by masterkey" %(schema),con)
        self.portfolios = list(output1["masterkey"].values)
        # update [MIR_WS].[dbo].[tablaOpciones]
        # set masterKey = CONCAT([Portfolio], [Parameter], [Transformation], [Differences], ' AR', [AR])
    def getPortfoliosSatus(self, request=None):
        self.availablePortfolios()
        output1 = pd.read_sql("select masterkey, CONCAT(currentprocessed,'/',totaloptions,' ',status) as status from %scurrentModels where `context`='%s' order by masterkey" %(schema,self.getContextSession(request)),con)
        portfoliosStatus = list(output1["status"].values)
        portfoliosKeys = list(output1["masterkey"].values)
        return zip(portfoliosKeys,portfoliosStatus)

    def loadScenarios(self):
        print("Loading Scenarios")
        self.scenarios = {}
        self.scenarios["Historic"] = pd.read_excel('PD Data.xlsx', index_col=0, sheet_name="Vars")
        self.scenarios["Base1"] = pd.read_excel('Base1 Data.xlsx', index_col=0, sheet_name="Vars")
        self.scenarios["Base"] = pd.read_excel('Base Data.xlsx', index_col=0, sheet_name="Vars")
        self.scenarios["Base3"] = pd.read_excel('Base3 Data.xlsx', index_col=0, sheet_name="Vars")

    def getScenario(self,scenario=""):
        return self.scenarios[scenario]

    def getSessionInfo(self, request):
        info = dict()
        info["currentContext"] = self.getContextSession(request)
        info["context"] = self.getContext()
        return info

#params = urllib.quote_plus('DRIVER={SQL Server};SERVER=localhost;DATABASE=MIR_WS;UID=sa;PWD=Cocoliso0)')
#engine = create_engine("mssql+pyodbc:///?odbc_connect=%s" % params)
#engine = create_engine('postgresql://bbomylezseqnuw:01a5f33037351e96dc0faca6a674e69042dd1a765d29b7b770063663eac85ebe@ec2-184-72-237-95.compute-1.amazonaws.com:5432/d6setjiqb9p7kn')
pymysql.converters.encoders[np.float64] = pymysql.converters.escape_float
pymysql.converters.conversions = pymysql.converters.encoders.copy()
pymysql.converters.conversions.update(pymysql.converters.decoders)
engine = create_engine('mysql+pymysql://epz3ofwjth0uo2nj:rwrv0fo3rkd4ce60@j1r4n2ztuwm0bhh5.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/rnqd4v5frbs2v9rn')
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

def setCurrentContext(request):
    chosenContext = request.GET.get("context",None)
    mainPersistence.setContextSession(chosenContext, request)
    return HttpResponse('Ok') #Correceted

@login_required(login_url='/login')
def portal(request):
    return portfoliosModels(request)
	
@login_required(login_url='/login')
def dependentVariables(request):
    documentos = os.listdir('./Contexts/%s' %(mainPersistence.getContextSession(request)))
    template = loader.get_template('dependentVariablesTable.html')
    print(documentos)
    existsPdExcel = ("PD Data.xlsx" in documentos)
    existsLGDExcel = ("LGD Data.xlsx" in documentos)
    responseInfo = {'existsPdExcel':existsPdExcel,'existsLGDExcel':existsLGDExcel}
    responseInfo.update(mainPersistence.getSessionInfo(request))
    return HttpResponse(template.render(responseInfo,request))
	
@login_required(login_url='/login')
def independentVariables(request):
    documentos = os.listdir('./Contexts/%s' %(mainPersistence.getContextSession(request)))
    template = loader.get_template('independentVariablesTable.html')
    print(documentos)
    existsBaseExcel = ("Base Data.xlsx" in documentos)
    existsBase1Excel = ("Base1 Data.xlsx" in documentos)
    existsBase2Excel = ("Base2 Data.xlsx" in documentos)
    existsBase3Excel = ("Base3 Data.xlsx" in documentos)
    existsSASExcel = ("SAS Data.xlsx" in documentos)
    responseInfo = {'existsBaseExcel':existsBaseExcel,
                                        'existsBase1Excel':existsBase1Excel,
                                        'existsBase2Excel':existsBase2Excel,
                                        'existsBase3Excel':existsBase3Excel,
                                        'existsSASExcel':existsSASExcel}
    responseInfo.update(mainPersistence.getSessionInfo(request))
    return HttpResponse(template.render(responseInfo,
                        request))

@login_required(login_url='/login')
def downloadPDData(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/PD Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=PD Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadLGDData(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/LGD Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=LGD Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBaseData(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBase1Data(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base1 Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base1 (Best) Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBase2Data(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base2 Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base2 (Pseudo-Base) Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadBase3Data(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base3 Data.xlsx', 'rb') as archivo:
        response = HttpResponse(archivo.read())
        response['content_type'] = 'application/xlsx'
        response['Content-Disposition'] = 'attachment;filename=Base3 (Worst) Data.xlsx'
        return response
    portal(request)

@login_required(login_url='/login')
def downloadSASData(request):
    with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/SAS Data.xlsx', 'rb') as archivo:
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
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/PD Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['PDDependent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('dependent') #Correceted

@login_required(login_url='/login')
def uploadLGDfile(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["LGDDependent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/LGD Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['LGDDependent']).chunks():
                    destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('dependent') # Corrected

@login_required(login_url='/login')
def uploadBasefile(request):
    if request.method == 'POST':
        # form = UploadFileForm(request.POST, request.FILES)
        fileName = str(request.FILES["BaseIndependent"])
        name, extension = fileName.split(".")
        if extension == 'xlsx':
            print("okey! - It's an excel file")
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base Data.xlsx', 'wb+') as destination:
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
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base1 Data.xlsx', 'wb+') as destination:
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
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base2 Data.xlsx', 'wb+') as destination:
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
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/Base3 Data.xlsx', 'wb+') as destination:
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
            with open('./Contexts/%s' %(mainPersistence.getContextSession(request))+'/SAS Data.xlsx', 'wb+') as destination:
                 for chunk in (request.FILES['SASIndependent']).chunks():
                     destination.write(chunk)
        else:
            print("Error - It's not an excel file (.xlsx)")
    return HttpResponseRedirect('independent')
	
@login_required(login_url='/login')
def portfoliosModels(request):
    salida = pd.read_sql("select * from %scurrentModels order by Portfolio, Parameter, Transformation, Differences, AR" %(schema),con)
    template = loader.get_template('portfoliosOptions.html')
    responseInfo = {'data':salida[["Portfolio","Parameter","Transformation","Differences","AR"]].to_html()}
    responseInfo.update(mainPersistence.getSessionInfo(request))
    return HttpResponse(template.render(responseInfo,request))
	
@login_required(login_url='/login')
def findModel(request):
    salida = pd.read_sql('select distinct `First Group`, `Second Group`, `Third Group` from %stablaModelos where `context` = "%s"' %(schema, mainPersistence.getContextSession(request)),con)
    template = loader.get_template('portfoliosOptions.html')
    responseInfo = {'data':salida.to_html(),'options1':mainPersistence.getOptions1(request=request),
                                                                'options2':mainPersistence.getOptions2(request=request),
                                                                'options3':mainPersistence.getOptions3(request=request),
                                                                'portfolios':mainPersistence.getPortfolios(request=request),'findModelEnabled':True}
    responseInfo.update(mainPersistence.getSessionInfo(request))
    return HttpResponse(template.render(responseInfo,request))

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
    responseInfo = {'portfolios':mainPersistence.getPortfoliosSatus(request=request)}
    responseInfo.update(mainPersistence.getSessionInfo(request))
    return render(request, 'execution.html', responseInfo)


@login_required(login_url='/login')
def executePortfolio(request):
    portfolioKey = request.GET.get("portfolio",None)
    print("Portfolio to queue %s" %(portfolioKey))
    p = threading.Thread(target=executePortfolioConcurrent, args=(portfolioKey,mainPersistence.getContextSession(request)))
    print("Starting Thread")
    p.start()
    return JsonResponse({"status":"Executing"})

def executePortfolioConcurrent(portfolioKey, contextName):
    print("Portfolio selected = %s" %(portfolioKey))
    # Configuration Part
    numberOfAR = 2
    portfolioKey = " Commercial - C&I LGDLogitdifQoQ AR1"
    # usedVariables = ["GDPR_logdifa","Sovereign1yA","Sovereign1yA_difa","Unemployment","Unemployment_difa"]
    usedVariables = ["GDPR_logdifQ","Sovereign1yA","Sovereign1yA_difa","Unemployment","Unemployment_difQ"]
    transformation = "LogitDiff"
    depVariable = "PD"
    dependentVariableAnalysis = "%s_%s" %(depVariable, transformation)
    output1 = pd.read_sql("select * from currentModels where masterKey='%s'" %(portfolioKey),con)
    infoPortfolio = output1.iloc[0]
    portfolio = str(infoPortfolio["Portfolio"]).strip()
    parameter = infoPortfolio["Parameter"]
    transformation = infoPortfolio["Transformation"]
    datosBase = mainPersistence.getScenario(scenario="Base")
    listado = [["GDPR",1],
               ["Unemployment",1],
                ["HPI",3],
                ["OilPrices",3],
                ["Sovereign1yA",2],
                ["Sovereign10yA",2],
                ["Sovereign1yQ",2],
                ["Sovereign10yQ",2],
                ["BBBSpread",2],
                ["CRE",3],
                ["PD_logit",4]]

    grupos = ["Listado de grupos",set([None]),set([None]),set([None]),set([None])]
    eliminar = ["_m1","_m2","_m3","_m4","_p1","_p2","_p3","_p4"]
    for k in datosBase.columns:
        for j in listado:
            if (j[0] in k):
                for i in eliminar:
                    k = k.replace(i,"")
                if k in usedVariables:
                    grupos[j[1]].add(k)
    newDf = pd.DataFrame(mainPersistence.getScenario("Historic")[portfolio])
    newDf["PD_Logit"] = newDf[portfolio].apply(lambda x: math.log(x/(1-x)))

    datosBase["PD_Logit"] = newDf["PD_Logit"]
    datosBase["PD_Logit_AR1"] = datosBase["PD_Logit"].shift(1)
    datosBase["PD_LogitDiff"] = datosBase["PD_Logit"] - datosBase["PD_Logit_AR1"]
    datosBase["PD_Logit_AR2"] = datosBase["PD_Logit"].shift(2)
    datosBase["PD_LogitDiff_AR1"] = datosBase["PD_LogitDiff"].shift(1)
    datosBase["PD_LogitDiff_AR2"] = datosBase["PD_LogitDiff"].shift(2)
    datosBase["PD"] = newDf[portfolio]

    dfg1 = pd.DataFrame({'key':[1 for k in range(len(grupos[1]))],'key1':[1 for k in range(len(grupos[1]))],"First Group":list(grupos[1])})
    dfg1.loc[dfg1["First Group"].isnull(),["key1"]] = 0
    dfg2 = pd.DataFrame({'key':[1 for k in range(len(grupos[2]))],'key2':[1 for k in range(len(grupos[2]))],"Second Group":list(grupos[2])})
    dfg2.loc[dfg2["Second Group"].isnull(),["key2"]] = 0
    dfg3 = pd.DataFrame({'key':[1 for k in range(len(grupos[3]))],'key3':[1 for k in range(len(grupos[3]))],"Third Group":list(grupos[3])})
    dfg3.loc[dfg3["Third Group"].isnull(),["key3"]] = 0
    Aux1 = pd.merge(pd.merge(dfg1,dfg2,on='key'),dfg3, on='key')
    dfAR = pd.DataFrame({'key':[1 for k in range(len(grupos[4]))],"AR Group":numberOfAR})
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

    print("length1: %s" %(len(Aux1)))
    Aux1 = pd.merge(Aux1,dfg1Ini,on='key1')
    Aux1 = pd.merge(Aux1,dfg1Fin,on='key1')
    print('First group merged')
    print("length2: %s" %(len(Aux1)))
    Aux1 = pd.merge(Aux1,dfg2Ini,on='key2')
    Aux1 = pd.merge(Aux1,dfg2Fin,on='key2')
    print('Second group merged')
    print("length3: %s" %(len(Aux1)))
    Aux1 = pd.merge(Aux1,dfg3Ini,on='key3')
    Aux1 = pd.merge(Aux1,dfg3Fin,on='key3')
    print('Third group merged')
    print("length4: %s" %(len(Aux1)))
    Aux1 = Aux1.loc[((Aux1['lag_1Fin'] >= Aux1['lag_1Ini']) | Aux1['First Group'].isnull())
                    & ((Aux1['lag_2Fin'] >= Aux1['lag_2Ini']) | Aux1['Second Group'].isnull())
                   & ((Aux1['lag_3Fin'] >= Aux1['lag_3Ini']) | Aux1['Third Group'].isnull())]
    print("length6: %s" %(len(Aux1)))
    numeroVars = 16
    for k in range(0, numeroVars, 1):
        Aux1["Var"+str(k)] = ''
        Aux1["Coef"+str(k)] = ''
    Aux1 = Aux1.reset_index()
    model1 = None
    query = "update currentModels set currentProcessed=0,  totalOptions=%s where masterKey='%s'" %(str(len(Aux1.index)),portfolioKey)
    con.execute(query)
    print(query)

    def functioncilla(x):
        global cleaned_data
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

        variables = [dependentVariableAnalysis] 
        if numberOfAR>0:
            opciones =  [dependentVariableAnalysis+"_AR1"] + opciones
        if numberOfAR>1:
            opciones =  [dependentVariableAnalysis+"_AR2"] + opciones
        variables = variables + opciones
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
        #print(stringVars)
        model1 = smf.ols(formula=stringVars,data=cleaned_data).fit()
        x["Var0"] = "Intercept"
        x["Coef0"] = model1.params["Intercept"]
        for k in range(1, len(opciones)+1, 1):
            #print("Saving %s" %(opciones[k-1]))
            x["Var"+str(k)] = opciones[k-1]
            x["Coef"+str(k)] = model1.params[opciones[k-1]]
        x["AIC"] = model1.aic
        x["F-pvalue"] = model1.f_pvalue
        x["R2"] = model1.rsquared
        x["MSE"] = model1.mse_model
        x["Transformation"] = transformation
        x["Portfolio"] = portfolio
        x["context"] = contextName

        #print("%s - %s" %(portfolioKey,x.name))

        if int(x.name)%1000 == 0:
            print("%s Progress: %s" %(portfolio,str(x.name)))
            #con.execute("update tablaOpciones set currentProcessed=%s where masterKey='%s'" %(str(int(x.name)+1),portfolioKey))

        return x

    timeInit = datetime.datetime.now()
    print(timeInit)
    salida = pd.DataFrame(Aux1.apply(functioncilla, axis=1))
    print("Total time: %s" %(datetime.datetime.now()-timeInit))
    query = "update %scurrentModels set currentprocessed=%s,  totaloptions=%s where masterkey='%s'" %(schema, str(len(Aux1.index)),str(len(Aux1.index)),portfolioKey)
    con.execute(query)
    #query = "delete from %stablaModelos where masterkey ='%s'" %(schema, portfolioKey)
    #con.execute(query)
    # Only for PostgreSQL
    print(salida.to_sql(con=con, name='tablaModelos', if_exists='replace'))
    del Aux1
    mainPersistence.loadVarsOptions()




def predict(coefs=None, years=20, transformation="", historic=None, scenarioData=None, portfolio="Commercial - C&I", minDate="2009-1Q"):
    output = []
    labels = []
    if (coefs is None or historic is None or scenarioData is None):
        return None
    print("Running Forecasting")
    scenarioData["Quarter"] = scenarioData.index
    ar1 = 0.0
    ar2 = 0.0
    ar1Logit = 0.0
    ar2Logit = 0.0
    ar1Logitdiff = 0.0
    ar2Logitdiff = 0.0
    logdiff = 0.0
    for index, row in scenarioData.iterrows():
        try:
            historicPoint = historic.loc[historic.index==index,[portfolio]].values[0][0]
            if math.isnan(historicPoint):
                continue
            historicPointLogit = math.log(historicPoint/(1-historicPoint))
            logdiff = historicPointLogit-ar1Logit
        except:
            #print(ValueError)
            historicPoint = float('NaN')
            historicPointLogit = float('NaN')
            logdiff = float('NaN')
        #print("%s Historic Point=%s, Historic Point Logit=%s, AR1=%s, AR2=%s, AR1Logit=%s, AR2Logit=%s, logdiff=%s, ar1Logitdiff=%s, ar2LogitDiff=%s" %(index,historicPoint, historicPointLogit,ar1,ar2,ar1Logit,ar2Logit,logdiff,ar1Logitdiff,ar2Logitdiff))
        y = 0
        maxVars = 18
        for k in range(0,maxVars):
            varName = coefs.iloc[0]["Var"+str(k)]
            if varName=="":
                break
            coefficient = float(coefs.iloc[0]["Coef"+str(k)])
            #print("Variable %s with coefficient %s" %(varName, coefficient))
            if varName=="Intercept":
                y= y+coefficient
                continue
            if varName[-3:-1]=="AR":
                if transformation == "Logitdiff":
                    if varName[-1:]=="1":
                        y = y+ar1Logitdiff*coefficient
                    if varName[-1:]=="2":
                        y = y+ar2Logitdiff*coefficient
                    continue

            y = y+(coefficient*float(scenarioData.loc[index,coefs.iloc[0]["Var"+str(k)]]))
        #print(y)
        ar2 = ar1
        ar2Logit = ar1Logit
        ar2Logitdiff = ar1Logitdiff
        if math.isnan(y) or len(output)>years*4:
            continue
        if math.isnan(historicPoint):
            ar1Logitdiff = 0.0
            if transformation=="Logit":
                ar1 = math.exp(y)/(1+math.exp(y))
            elif transformation=="Logitdiff":
                ar1 = math.exp(y+ar1Logit)/(1+math.exp(y+ar1Logit))
            else:
                ar1 = y
            ar1Logit = math.log(ar1/(1-ar1))
            ar1Logitdiff = ar1Logit - ar2Logit
        else:
            ar1 = historicPoint
            ar1Logitdiff = historicPointLogit - ar1Logit
            ar1Logit = historicPointLogit
        if index < minDate:
            ar2Logit = 0.0
            ar2LogitDiff = 0.0
            continue
        #print("Calculated value for period %s = %s" %(index, y))
        #if transformation=="Logit":
        #    y=math.exp(y)/(1+math.exp(y))
        #elif transformation=="Logitdiff":
        #y=math.exp(y+ar1Logit)/(1+math.exp(y+ar1Logit))
            #print(y)
            #output.append("")
        else:
            labels.append(row["Quarter"])
            output.append(round(ar1*100,2))
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
    series["Base"], labels = predict(coefs=salida,transformation="Logitdiff",historic=mainPersistence.getScenario(scenario="Historic"),
            scenarioData=mainPersistence.getScenario(scenario="Base"))
    series["Base1"], labels = predict(coefs=salida,transformation="Logitdiff",historic=mainPersistence.getScenario(scenario="Historic"),
            scenarioData=mainPersistence.getScenario(scenario="Base1"))
    series["Base3"], labels = predict(coefs=salida,transformation="Logitdiff",historic=mainPersistence.getScenario(scenario="Historic"),
            scenarioData=mainPersistence.getScenario(scenario="Base3"))
    series["Historical"] = labels
    historical = mainPersistence.getScenario(scenario="Historic")
    series["Training"] = [round(x[0]*100,2) for x in historical.loc[historical.index.isin(labels),["Commercial - C&I"]].values.tolist()]
    #series["Historical"] = list(mainPersistence.getScenario(scenario="Base").index.values)
    #print(list(series["Base"].values))
    return JsonResponse({"Base":series["Base"],
                        "Base1":series["Base1"],
                        "Base3":series["Base3"],
                        "labels":series["Historical"],
                        "Historical":series["Training"],
                        "statistics":getStatistics(salida.iloc[0]),
                        "coefficients":getCoefficients(salida.iloc[0])})