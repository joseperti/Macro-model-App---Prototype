# -*- coding: utf-8 -*-

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.portal),
    url('logout', views.logoutAccess),
    url('login', views.loginAccess),
	url('PDData',views.downloadPDData),
	url('LGDData',views.downloadLGDData),
	url('BaseData',views.downloadBaseData),
	url('Base1Data',views.downloadBase1Data),
	url('Base2Data',views.downloadBase2Data),
	url('Base3Data',views.downloadBase3Data),
	url('SASData',views.downloadSASData),
	url('portal', views.portal),
	url('execution', views.execution),
	url('independent', views.independentVariables),
	url('dependent', views.dependentVariables),
	url('uploadPDfile', views.uploadPDfile),
	url('uploadLGDfile', views.uploadLGDfile),
	url('uploadBasefile', views.uploadBasefile),
	url('uploadBase1file', views.uploadBase1file),
	url('uploadBase2file', views.uploadBase2file),
	url('uploadBase3file', views.uploadBase3file),
	url('uploadSASfile', views.uploadSASfile),
	url('portfoliosModels', views.portfoliosModels),
	url('findModel', views.findModel),
	url('ajax/refreshTable/', views.refreshTable),
	url('ajax/modelProjection/', views.modelProjection),
	url('ajax/executePortfolio/', views.executePortfolio),
	url('ajax/setCurrentContext/', views.setCurrentContext)
]