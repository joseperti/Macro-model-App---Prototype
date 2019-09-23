######################################################################################################################################################################
#
# `7MM"""Yp, `7MM"""Yp, `7MMF'   `7MF' db            .g8"""bgd `7MM"""YMM    .g8"""bgd `7MMF'          `7MMM.     ,MMF'                                  
#   MM    Yb   MM    Yb   `MA     ,V  ;MM:         .dP'     `M   MM    `7  .dP'     `M   MM              MMMb    dPMM                                    
#   MM    dP   MM    dP    VM:   ,V  ,V^MM.        dM'       `   MM   d    dM'       `   MM              M YM   ,M MM   ,6"Yb.  ,p6"bo `7Mb,od8 ,pW"Wq.  
#   MM"""bg.   MM"""bg.     MM.  M' ,M  `MM        MM            MMmmMM    MM            MM              M  Mb  M' MM  8)   MM 6M'  OO   MM' "'6W'   `Wb 
#   MM    `Y   MM    `Y     `MM A'  AbmmmqMA       MM.           MM   Y  , MM.           MM      ,       M  YM.P'  MM   ,pm9MM 8M        MM    8M     M8 
#   MM    ,9   MM    ,9      :MM;  A'     VML      `Mb.     ,'   MM     ,M `Mb.     ,'   MM     ,M       M  `YM'   MM  8M   MM YM.    ,  MM    YA.   ,A9 
# .JMMmmmd9  .JMMmmmd9        VF .AMA.   .AMMA.      `"bmmmd'  .JMMmmmmMMM   `"bmmmd'  .JMMmmmmMMM     .JML. `'  .JMML.`Moo9^Yo.YMbmd' .JMML.   `Ybmd9'  
#
# Author: BBVA GRM Analytics
# Contact:
# Date: 20180920
# Notes:
# Usage:
#
######################################################################################################################################################################

# PROGRESS BAR
pb <- winProgressBar(title="Step 2. Status", label="Starting", min=0, max=100, initial=0)

library(lmtest)


#-------------------------------------
# Install Libraries
# Note: Uncomment for install libraries.
#-------------------------------------
#install.packages("xlsx")
#install.packages("rJava")
#install.packages("rngWELL") 
#install.packages("randtoolbox") 
#install.packages("XLConnect")
#install.packages("nortest")
#install.packages("strucchange")
#install.packages("goftest") 
#install.packages("XLConnectJars") 
#install.packages("xlsxjars")  
#install.packages("excel.link")
#install.packages("tseries")
#install.packages("permute")
#install.packages("car")
#install.packages("lmtest")

#-------------------------------------
# Load Libraries
#-------------------------------------
setWinProgressBar(pb, 5, label='Loading Libraries =(') 
#require(xlsx)
library(zoo)
 
#library(xlsxjars) 
#library(xlsx) 
library(rngWELL) 
library(randtoolbox) 
#library(XLConnectJars) 
#library(XLConnect) 
library(excel.link)
library(tseries)
library(permute)
library(car)
library(nortest)
library(lmtest)
library(foreach)
library(parallel)
library(doParallel)
library(doSNOW)
library(strucchange)


workingdir <- "C:/Users/xs15354/Desktop/Tool June 2019"
#-------------------------------------
wb_name = "BBVA CECL Macro Model Tool DS1.xlsm"
Sys.setenv(JAVA_HOME='C:/Program Files/Java/jre1.8.0_101/')

setwd(workingdir)
#getwd()
### - Activate workbook
#wb_name = "BBVA CECL Macro Model Tool.xlsm"
xls = xl.get.excel()
xl.workbook.activate(wb_name)

#-------------------------------------
# Shift fuction for lags and leads:
#-------------------------------------
setWinProgressBar(pb, 10, label='Loading Shift Function') 

shift<-function(x,shift_by){
  stopifnot(is.numeric(shift_by))
  stopifnot(is.numeric(x))
  
  if (length(shift_by)>1)
    return(sapply(shift_by,shift, x=x))
  
  out<-NULL
  abs_shift_by=abs(shift_by)
  if (shift_by > 0 )
    out<-c(tail(x,-abs_shift_by),rep(NA,abs_shift_by))
  else if (shift_by < 0 )
    out<-c(rep(NA,abs_shift_by), head(x,-abs_shift_by))
  else
    out<-x
  out
}


adt <- function(x){test<-ad.test(x); return(test$p.value)}
#-------------------------------------
# Reads XLS book
#-------------------------------------

setWinProgressBar(pb, 15, label='Reading Dependent Variables List') 
p10_depvar_list <- xl.read.file(filename = wb_name, xl.sheet = "Step 1", top.left.cell = 'B14', excel.visible = FALSE, col.names = TRUE, row.names = FALSE)
setWinProgressBar(pb, 20, label='Reading Independent Variables List') 
p20_indvar_list <- xl.read.file(filename = wb_name, xl.sheet = "Step 1", top.left.cell = 'L10', excel.visible = FALSE, col.names = TRUE, row.names = FALSE)
setWinProgressBar(pb, 25, label='Reading Dependent Variables Transformations List') 
t10_depvar_list <- xl.read.file(filename = wb_name, xl.sheet = "Step 1", top.left.cell = 'C10', excel.visible = FALSE, col.names = TRUE, row.names = FALSE)


# Build the LIST tables for the selected variables, as a subset of the output for Step 1.
p10_t <- data.frame(p10_depvar_list)
p11_depvar_list <- subset(p10_t, p10_t[,1] == 'x')

p20_t <- data.frame(p20_indvar_list)
p21_indvar_list <- subset(p20_t, p20_t[,1] == 'x')

# Build the DATA tables for the selected variables, as a subset of the output for Step 1.
setWinProgressBar(pb, 30, label='Reading Dependent Variables Transformations Data') 
p10_depvar_data <- xl.read.file(filename = wb_name, xl.sheet = "S1.OutputsDep", top.left.cell = 'C4', excel.visible = FALSE, col.names = TRUE, row.names = FALSE)
p10_data_t <- data.frame(p10_depvar_data)
p11_depvar_data <- p10_data_t[,p11_depvar_list$Name.of.the.variable]

setWinProgressBar(pb, 35, label='Reading Independent Variables Transformations Data') 
p20_indvar_data <- xl.read.file(filename = wb_name, xl.sheet = "S1.OutputsInd", top.left.cell = 'C4', excel.visible = FALSE, col.names = TRUE, row.names = FALSE)
p20_data_t <- data.frame(p20_indvar_data)
#p21_indvar_data <- p20_data_t[,p21_indvar_list$Name.of.the.variable]
if(length(p21_indvar_list$Name.of.the.variable)==1){
  p21_indvar_data <- data.frame(p20_data_t[,p21_indvar_list$Name.of.the.variable])
  names(p21_indvar_data)[1] <- p21_indvar_list$Name.of.the.variable
} else {
  p21_indvar_data <- p20_data_t[,p21_indvar_list$Name.of.the.variable]
}

setWinProgressBar(pb, 40, label='Reading Signs Table') 
signs_table <- xl.read.file(filename = wb_name, xl.sheet = "S0.SignsGroups", top.left.cell = 'B2', excel.visible = FALSE, col.names = TRUE, row.names = TRUE)

# Load lag/lead options
setWinProgressBar(pb, 45, label='Reading Lags Table') 
lags_table <- xl.read.file(filename = wb_name, xl.sheet = "Step 2", top.left.cell = 'G2', excel.visible = FALSE, col.names = TRUE, row.names = TRUE)
setWinProgressBar(pb, 50, label='Reading Leads Table') 
leads_table <- xl.read.file(filename = wb_name, xl.sheet = "Step 2", top.left.cell = 'J2', excel.visible = FALSE, col.names = TRUE, row.names = TRUE)

setWinProgressBar(pb, 55, label='Reading Filters') 
filters_table <- xl.read.file(filename = wb_name, xl.sheet = "Step 2", top.left.cell = 'F7', excel.visible = FALSE, col.names = TRUE, row.names = TRUE)
AICfilter <- filters_table['Top AIC models','Filters']
pvalfilter <- filters_table['p-value threshold','Filters']
pvalFfilter <- filters_table['p-value F','Filters']
Rsquaredfilter <- filters_table['Rsquared','Filters']
zerofilter <- filters_table['zeromean','Filters']
AndDarlingfilter <- filters_table['Anderson-Darling','Filters']
BrPagenfilter <- filters_table['Breusch-Pagen','Filters']
BrGodfreyfilter <- filters_table['Breusch-Godfrey','Filters']
NybHansenfilter <- filters_table['Nyblom-Hansen','Filters']


#-------------------------------------
# Builds all the model combinations
#-------------------------------------
setWinProgressBar(pb, 60, label='Building all Model Combinations') 

# Make lists of variables by groups, including NaN, which allows models of 1, 2 and 3 variables.
#p11_depvar_list
p21_indvar_1_list <-  c(subset(p21_indvar_list,p21_indvar_list[,6]==1)$Name.of.the.variable, NaN)
p21_indvar_2_list <-  c(subset(p21_indvar_list,p21_indvar_list[,6]==2)$Name.of.the.variable, NaN)
p21_indvar_3_list <-  c(subset(p21_indvar_list,p21_indvar_list[,6]==3)$Name.of.the.variable, NaN)

# Make combinations of variables to identify all candidate models.
p30_models_list <- expand.grid(p11_depvar_list$Name.of.the.variable,p21_indvar_1_list, p21_indvar_2_list, p21_indvar_3_list)

# Make combinations of dependent and independent variables, for the lag/leads analysis.
p21_indvar_T_list <- c(subset(p21_indvar_list,p21_indvar_list[,6]==1)$Name.of.the.variable,subset(p21_indvar_list,p21_indvar_list[,6]==2)$Name.of.the.variable,subset(p21_indvar_list,p21_indvar_list[,6]==3)$Name.of.the.variable)
p21_indvar_comb <- expand.grid(p11_depvar_list$Name.of.the.variable,p21_indvar_T_list)

# Make combinations of lags for the whole model
maxlag_dep <- lags_table['Dependent Variable','Autoregressive']
maxlag_ind <- leads_table['Independent Variable','Lags']
maxlead_ind <- leads_table['Independent Variable','Leads']
complete_lag_comb <- expand.grid('lagdep',(-maxlag_ind):(maxlead_ind),(-maxlag_ind):(maxlead_ind),(-maxlag_ind):(maxlead_ind),(-maxlag_ind):(maxlead_ind),(-maxlag_ind):(maxlead_ind),(-maxlag_ind):(maxlead_ind))
complete_lag_comb <- subset(complete_lag_comb, Var2<=Var3 & Var4<=Var5 & Var6<=Var7 & Var3>=-1 & Var5>=-1 & Var7>=-1)

#-------------------------------------
# Dependent Variables. Lag Analysis
#-------------------------------------
setWinProgressBar(pb, 65, label='Lag Analysis: Dependent Variables') 

# Dependent Variables. A5.
df <- data.frame(matrix(ncol = 4, nrow = length(p11_depvar_list$Name.of.the.variable)*maxlag_dep))
dim(df)

# Dependent Variables. Summary. F5.
df_s <- data.frame(matrix(ncol = 2, nrow = length(p11_depvar_list$Name.of.the.variable)))
dim(df_s)

# Loop through the variables
for(t in 1: length(p11_depvar_list$Name.of.the.variable)) {
  #t=1
  name <- p11_depvar_list$Name.of.the.variable[t]
  if(length(p11_depvar_list$Name.of.the.variable)==1){
    data <- p11_depvar_data
  } else {
    data <- p11_depvar_data[name]
  }
  
  nlags <- 0
  last_aic <- 1000
  
  data_lag_tot <- data.frame(embed(unlist(data),maxlag_dep+1))
  
  if(maxlag_dep>0){
    
    #Loop through the possible lags
    for(l in 1:maxlag_dep){
      #l=1  
      
      xnam <- paste("X", 2:(l+1), sep="")
      fmla <- as.formula(paste("X1 ~ ", paste(xnam, collapse= "+")))
      model <- lm(fmla, data = data_lag_tot, na.action=na.exclude)
      # Instead of AIC we are using AICc, which takes into account the number of parameters
      # and number of observations, allowing that way samples of different size, and prioritizing
      # those with less variables.
      k <- length(coefficients(model))
      n <- nobs(model)
      model_aic <- AIC(model) + 2*(k*k+k)/(n-k-1)
      #sum(model$residuals^2)
      if(model_aic < last_aic){
        last_aic <- model_aic
        nlags <- l
      }
      
      row <- (t-1)*maxlag_dep+(l-1+1)
            
      df[row,1] <- name
      df[row,2] <- model_aic
      df[row,4] <- l
      
      }
  }  
  df_s[t,1] <- name
  df_s[t,2] <- nlags
}

#-------------------------------------
# Candidate Models. Populate master matrix
#-------------------------------------
setWinProgressBar(pb, 75, label='Obtaining Candidate Models') 

#df_stat <- (matrix(ncol = 59, nrow = (nrow(p30_models_list))*lengths(complete_lag_comb)[1]))
#dim(df_stat)

one_lag_comb <- expand.grid((-maxlag_ind):(maxlead_ind),(-maxlag_ind):(maxlead_ind))
one_lag_comb <- subset(one_lag_comb, Var1<=Var2) #& Var2>=-1




full_model_param <- (matrix(ncol = 11, nrow = nrow(p30_models_list)*lengths(one_lag_comb)[1]*lengths(one_lag_comb)[1]*lengths(one_lag_comb)[1]))
dim(full_model_param)

r <- 1
nrowp30<-nrow(p30_models_list)
for(z in 1:nrowp30) {
  setWinProgressBar(pb, 75, label=paste('Obtaining Candidate Models ', round(z*100/nrowp30)," %.") )
  #z=1
  n_dep <- paste(p30_models_list$Var1[z],"",sep="")
  n_ind_1 <- paste(p30_models_list$Var2[z],"",sep="")
  n_ind_2 <- paste(p30_models_list$Var3[z],"",sep="")
  n_ind_3 <- paste(p30_models_list$Var4[z],"",sep="")
  for(m1 in 1:lengths(one_lag_comb)[1]) { #var1
    if(n_ind_1!='NaN'){
      m1_1 <- one_lag_comb$Var1[m1]
      m1_2 <- one_lag_comb$Var2[m1]
    } else {
      m1_1 <- 'NaN'
      m1_2 <- 'NaN'
    }
    for(m2 in 1:lengths(one_lag_comb)[1]) { #var2
      if(n_ind_2!='NaN'){
        m2_1 <- one_lag_comb$Var1[m2]
        m2_2 <- one_lag_comb$Var2[m2]
      } else {
        m2_1 <- 'NaN'
        m2_2 <- 'NaN'
      }
      for(m3 in 1:lengths(one_lag_comb)[1]) { #var2
        if(n_ind_3!='NaN'){
          m3_1 <- one_lag_comb$Var1[m3]
          m3_2 <- one_lag_comb$Var2[m3]
        } else {
          m3_1 <- 'NaN'
          m3_2 <- 'NaN'
        }
        full_model_param[r, 1] <- paste(p30_models_list$Var1[z],"",sep="")
        full_model_param[r, 2] <- df_s[df_s$X1==paste(p30_models_list$Var1[z],"",sep=""),2]
        full_model_param[r, 3] <- paste(p30_models_list$Var2[z],"",sep="")
        full_model_param[r, 4] <- m1_1
        full_model_param[r, 5] <- m1_2
        full_model_param[r, 6] <- paste(p30_models_list$Var3[z],"",sep="")
        full_model_param[r, 7] <- m2_1
        full_model_param[r, 8] <- m2_2
        full_model_param[r, 9] <- paste(p30_models_list$Var4[z],"",sep="")
        full_model_param[r, 10] <- m3_1
        full_model_param[r, 11] <- m3_2
        r <- r + 1
      }#for
    }#for
  }#for
}#for

dim(full_model_param)
full_model_param_unique <- unique(full_model_param[,],ordered=FALSE)
full_model_param_unique <- full_model_param_unique[!apply(is.na(full_model_param_unique), 1, all),]
dim(full_model_param_unique)

# Candidate Models. A2.
# df <- data.frame(matrix(ncol = 79, nrow = nrow(full_model_param_unique)))
# dim(df)
# df_stat <- (matrix(ncol = 59, nrow = nrow(full_model_param_unique)))
# dim(df_stat)

# Find the maximum common data for all models, to use as a common sample

nray=nrow(full_model_param_unique)

pb2 <- winProgressBar(title="Step 2. Status", label=paste("Calculating", nray, "Regressions"), min=0, max = nray)
progress <- function(n) setWinProgressBar(pb2, n)
opts <- list(progress = progress)
cluster <- makeCluster(detectCores())
registerDoSNOW(cluster)
getDoParWorkers()

dfa<-foreach(r=1:nray, .combine = 'rbind', .options.snow = opts ) %dopar% {
  #for(r in 1:nray){    
  dfch <- data.frame(matrix(ncol = 196, nrow = 1))
  
  #r=375
  
  # Retrieve already available information
  # ---------------------------------------
  dfch[1, 1] <- r
  #dfch[1,84+ 1] <- r
  dfch[1, 2:12] <- full_model_param_unique[r, 1:11]
  
  cat(paste(r,'out of', nrow(full_model_param_unique),'\n'))
  
  # Start running the regressions and extract parameters
  # -----------------------------------------------------
  
  name_d <- dfch[1, 2]
  name_i1 <- dfch[1, 4]
  name_i2 <- dfch[1, 7]
  name_i3 <- dfch[1, 10]
  
  # Damos una vuelta para manejar los NAs
  p21_indvar_data_na <- p21_indvar_data
  p21_indvar_data_na$'NaN' <- NA
  
  #cat(paste(name_d, "-", name_i1, "-", name_i2, "-", name_i3), "\n")
  #data <- p11_depvar_data[name_d]
  
  if(length(p11_depvar_list$Name.of.the.variable)==1){
    data <- data.frame(embed(unlist(p11_depvar_data),1))
  } else {
    data <- p11_depvar_data[name_d]
  }
  
  data_i1 <- p21_indvar_data_na[name_i1]
  data_i2 <- p21_indvar_data_na[name_i2]
  data_i3 <- p21_indvar_data_na[name_i3]
  names(data) <- "Y"
  names(data_i1) <- "X1"
  names(data_i2) <- "X2"
  names(data_i3) <- "X3"
  
  # Load in the same data frame all the series, for all possible lags and leads for Y, X1, X2 and X3
  data_lag_tot <- data
  data_lag_tot$X1m4 <- shift(data.matrix(data_i1),-4)
  data_lag_tot$X1m3 <- shift(data.matrix(data_i1),-3)
  data_lag_tot$X1m2 <- shift(data.matrix(data_i1),-2)
  data_lag_tot$X1m1 <- shift(data.matrix(data_i1),-1)
  data_lag_tot$X1 <- shift(data.matrix(data_i1), 0)
  data_lag_tot$X1p1 <- shift(data.matrix(data_i1),1)
  data_lag_tot$X1p2 <- shift(data.matrix(data_i1),2)
  data_lag_tot$X1p3 <- shift(data.matrix(data_i1),3)
  data_lag_tot$X1p4 <- shift(data.matrix(data_i1),4)
  
  data_lag_tot$X2m4 <- shift(data.matrix(data_i2),-4)
  data_lag_tot$X2m3 <- shift(data.matrix(data_i2),-3)
  data_lag_tot$X2m2 <- shift(data.matrix(data_i2),-2)
  data_lag_tot$X2m1 <- shift(data.matrix(data_i2),-1)
  data_lag_tot$X2 <- shift(data.matrix(data_i2), 0)
  data_lag_tot$X2p1 <- shift(data.matrix(data_i2),1)
  data_lag_tot$X2p2 <- shift(data.matrix(data_i2),2)
  data_lag_tot$X2p3 <- shift(data.matrix(data_i2),3)
  data_lag_tot$X2p4 <- shift(data.matrix(data_i2),4)
  
  data_lag_tot$X3m4 <- shift(data.matrix(data_i3),-4)
  data_lag_tot$X3m3 <- shift(data.matrix(data_i3),-3)
  data_lag_tot$X3m2 <- shift(data.matrix(data_i3),-2)
  data_lag_tot$X3m1 <- shift(data.matrix(data_i3),-1)
  data_lag_tot$X3 <- shift(data.matrix(data_i3), 0)
  data_lag_tot$X3p1 <- shift(data.matrix(data_i3),1)
  data_lag_tot$X3p2 <- shift(data.matrix(data_i3),2)
  data_lag_tot$X3p3 <- shift(data.matrix(data_i3),3)
  data_lag_tot$X3p4 <- shift(data.matrix(data_i3),4)
  
  data_lag_tot$Ym2 <- shift(data.matrix(data),-2)
  data_lag_tot$Ym1 <- shift(data.matrix(data),-1)  
  
  #Now select which ones we are going to use
  # X1
  #--------------------------------------------------------
  if(maxlead_ind>0){xname1_max=c(paste("X1m", maxlag_ind, sep=""),paste("X1p", maxlead_ind, sep=""))} else {xname1_max=paste("X1m", maxlag_ind, sep="")}
  if(maxlag_ind==0){xname1_max=c("X1",paste("X1p", maxlead_ind, sep=""))}
  if ((is.na(dfch[1,5])|dfch[1,5]=='NaN') & (is.na(dfch[1,6])|dfch[1,6]=='NaN')) {
    xname1=''
    xname1_max=''
  } else if (dfch[1,5]<0 & dfch[1,6]<0){
    # Case 1. Both negative.
    min_neg <- strtoi(dfch[1,5])
    max_neg <- strtoi(dfch[1,6])
    
    xname1 <- paste("X1m", (-as.numeric(min_neg)):(-as.numeric(max_neg)), sep="")
    
  } else if(dfch[1,5]<0 & dfch[1,6]>0) {
    # Case 2. Negative and Positive.
    min_neg <- strtoi(dfch[1,5])
    max_pos <- strtoi(dfch[1,6])
    xnam_n <- paste("X1m", seq(-as.numeric(min_neg), 1, by = -1) ,sep="")
    xnam_p <- paste("X1p", seq(1, max_pos, by = 1) ,sep="")
    xname1 <- c(xnam_n, "X1", xnam_p)
    
  } else if(dfch[1,5]>0 & dfch[1,6]>0) {
    # Case 3. Both positive.
    min_pos <- strtoi(dfch[1,5])
    max_pos <- strtoi(dfch[1,6])
    xname1 <- paste("X1p", seq(min_pos, max_pos, by = 1) ,sep="")
    
  } else if(dfch[1,5]<0 & dfch[1,6]==0) {
    # Case 4. Negative up to 0.
    min_neg <- as.numeric(dfch[1,5])
    xnam_n <- paste("X1m", seq(-min_neg, 1, by = -1) ,sep="")
    xname1 <- c(xnam_n, "X1")
    
  } else if(dfch[1,5]==0 & dfch[1,6]>0) { 
    # Case 5. Positive, starting from 0.
    max_pos <- dfch[1,6]
    xnam_p <- paste("X1p", seq(1, max_pos, by = 1) ,sep="")
    xname1 <- c("X1", xnam_p)
    
  } else if (dfch[1,5]==0 & dfch[1,6]==0) {
    # Case 6. Max and Min = 0
    xname1 <- "X1"
    xname1_max='X1'
  }
  
  # X2
  #--------------------------------------------------------
  if(maxlead_ind>0){xname2_max=c(paste("X2m", maxlag_ind, sep=""),paste("X2p", maxlead_ind, sep=""))} else {xname2_max=paste("X2m", maxlag_ind, sep="")}
  if(maxlag_ind==0){xname2_max=c("X2",paste("X2p", maxlead_ind, sep=""))}
  if ((is.na(dfch[1,8])|dfch[1,8]=='NaN') & (is.na(dfch[1,9])|dfch[1,9]=='NaN')) {
    xname2=''
    xname2_max=''
  } else if(dfch[1,8]<0 & dfch[1,9]<0){
    # Case 1. Both negative.
    min_neg <- strtoi(dfch[1,8])
    max_neg <- strtoi(dfch[1,9])
    xname2 <- paste("X2m", (-as.numeric(min_neg)):(-as.numeric(max_neg)), sep="")
    
  } else if(dfch[1,8]<0 & dfch[1,9]>0) {
    # Case 2. Negative and Positive.
    min_neg <- strtoi(dfch[1,8])
    max_pos <- strtoi(dfch[1,9])
    xnam_n <- paste("X2m", seq(-as.numeric(min_neg), 1, by = -1) ,sep="")
    xnam_p <- paste("X2p", seq(1, max_pos, by = 1) ,sep="")
    
    xname2 <- c(xnam_n, "X2", xnam_p)
  } else if(dfch[1,8]>0 & dfch[1,9]>0) {
    # Case 3. Both positive.
    min_pos <- strtoi(dfch[1,8])
    max_pos <- strtoi(dfch[1,9])
    xname2 <- paste("X2p", seq(as.numeric(min_pos), as.numeric(max_pos), by = 1) ,sep="")
    
  } else if(dfch[1,8]<0 & dfch[1,9]==0) {
    # Case 4. Negative up to 0.
    min_neg <- dfch[1,8]
    xnam_n <- paste("X2m", seq(-as.numeric(min_neg), 1, by = -1) ,sep="")
    xname2 <- c(xnam_n, "X2")
    
  } else if(dfch[1,8]==0 & dfch[1,9]>0) {
    # Case 5. Positive, starting from 0.
    max_pos <- dfch[1,9]
    xnam_p <- paste("X2p", seq(1, as.numeric(max_pos), by = 1) ,sep="")
    xname2 <- c("X2", xnam_p)
    
  } else if (dfch[1,8]==0 & dfch[1,9]==0) {
    # Case 6. Max and Min = 0
    xname2 <- "X2"
    xname2_max='X2'
  }
  # X3
  #--------------------------------------------------------
  if(maxlead_ind>0){xname3_max=c(paste("X3m", maxlag_ind, sep=""),paste("X3p", maxlead_ind, sep=""))} else {xname3_max=paste("X3m", maxlag_ind, sep="")}
  if(maxlag_ind==0){xname3_max=c("X3",paste("X3p", maxlead_ind, sep=""))}
  if ((is.na(dfch[1,11])|dfch[1,11]=='NaN') & (is.na(dfch[1,12])|dfch[1,12]=='NaN')) {
    xname3=''
    xname3_max=''
  } else if(dfch[1,11]<0 & dfch[1,12]<0){
    # Case 1. Both negative.
    min_neg <- strtoi(dfch[1,11])
    max_neg <- strtoi(dfch[1,12])
    xname3 <- paste("X3m", (-as.numeric(min_neg)):(-as.numeric(max_neg)), sep="")
    
  } else if(dfch[1,11]<0 & dfch[1,12]>0) {
    # Case 2. Negative and Positive.
    min_neg <- strtoi(dfch[1,11])
    max_pos <- strtoi(dfch[1,12])
    xnam_n <- paste("X3m", seq(-as.numeric(min_neg), 1, by = -1) ,sep="")
    xnam_p <- paste("X3p", seq(1, max_pos, by = 1) ,sep="")
    
    xname3 <- c(xnam_n, "X3", xnam_p)
  } else if(dfch[1,11]>0 & dfch[1,12]>0) {
    # Case 3. Both positive.
    min_pos <- strtoi(dfch[1,11])
    max_pos <- strtoi(dfch[1,12])
    xname3 <- paste("X3p", seq(as.numeric(min_pos), as.numeric(max_pos), by = 1) ,sep="")
    
  } else if(dfch[1,11]<0 & dfch[1,12]==0) {
    # Case 4. Negative up to 0.
    min_neg <- dfch[1,11]
    xnam_n <- paste("X3m", seq(-as.numeric(min_neg), 1, by = -1) ,sep="")
    
    xname3 <- c(xnam_n, "X3")
  } else if(dfch[1,11]==0 & dfch[1,12]>0) {
    # Case 5. Positive, starting from 0.
    max_pos <- dfch[1,12]
    xnam_p <- paste("X3p", seq(1, as.numeric(max_pos), by = 1) ,sep="")
    
    xname3 <- c("X3", xnam_p)
  } else if (dfch[1,11]==0 & dfch[1,12]==0) {
    # Case 6. Max and Min = 0
    xname3 <- "X3"
    xname3_max='X3'
  }
  # Y
  #--------------------------------------------------------
  max_neg <- strtoi(dfch[1,3])
  max_neg1 <- (dfch[1,4]=='NaN' & dfch[1,7]=='NaN'& dfch[1,10]=='NaN') 
  
  if(max_neg>0){
    yname <- paste("Ym", 1:(as.numeric(max_neg)), sep="")
  }      else{yname="1"}
  # Aqu�? hay que truncar data_lag_tot para que tenga para cada combinación de variables, el tamaño común de la muestra.
  # Por simplicidad voy a decir que sea:
  # + el número de observaciones de la variable más corta
  # - máximo número de lags
  # - máximo número de leads
  # As�? que voy a máximos, y luego me quedo con los datos utilizados para usar como muestra en el la segunda regresión buena.
  
  #fmla_max <- as.formula(paste("Y ~ ", paste(c(xname1_max, xname2_max, xname3_max, yname), collapse= "+")))
  #model_max <- lm(fmla_max, data = data_lag_tot, na.action=na.exclude)
  #model_common_data <- data_lag_tot[rownames(model_max$model),]
  fmla <- as.formula(paste("Y ~ ", paste(c(xname1, xname2, xname3, yname), collapse= "+")))
  
  #model <- lm(fmla, data = model_common_data, na.action=na.exclude)
  #codigo retocado
  
  list = union(union(union(union(xname1,xname2),xname3),yname),"Y")
  list2 = list[list != ""]
  list3 = list2[list2 != "1"]
  if (length(list3)==1){
    return(NA)
  }
  selectCol = data_lag_tot[,list3]
  cleaned_data_lag_tot=selectCol[complete.cases(selectCol),]
  
  #cleaned_data_lag_tot <- data_lag_tot[, colSums(is.na(data_lag_tot)) != nrow(data_lag_tot)]
  #cleaned_data_lag_tot <- cleaned_data_lag_tot[complete.cases(cleaned_data_lag_tot),]
  model <- lm(fmla, data = cleaned_data_lag_tot, na.action=na.exclude)
  
  #B0
  dfch[1, 13] <-  model$coefficients['(Intercept)']
  #X1
  dfch[1, 14] <-  model$coefficients['X1m4']
  dfch[1, 15] <-  model$coefficients['X1m3']
  dfch[1, 16] <-  model$coefficients['X1m2']
  dfch[1, 17] <-  model$coefficients['X1m1']
  dfch[1, 18] <-  model$coefficients['X1']
  dfch[1, 19] <-  model$coefficients['X1p1']
  dfch[1, 20] <-  model$coefficients['X1p2']
  dfch[1, 21] <-  model$coefficients['X1p3']
  dfch[1, 22] <-  model$coefficients['X1p4']
  #X2
  dfch[1, 23] <-  model$coefficients['X2m4']
  dfch[1, 24] <-  model$coefficients['X2m3']
  dfch[1, 25] <-  model$coefficients['X2m2']
  dfch[1, 26] <-  model$coefficients['X2m1']
  dfch[1, 27] <-  model$coefficients['X2']
  dfch[1, 28] <-  model$coefficients['X2p1']
  dfch[1, 29] <-  model$coefficients['X2p2']
  dfch[1, 30] <-  model$coefficients['X2p3']
  dfch[1, 31] <-  model$coefficients['X2p4']
  #X3
  dfch[1, 32] <-  model$coefficients['X3m4']
  dfch[1, 33] <-  model$coefficients['X3m3']
  dfch[1, 34] <-  model$coefficients['X3m2']
  dfch[1, 35] <-  model$coefficients['X3m1']
  dfch[1, 36] <-  model$coefficients['X3']
  dfch[1, 37] <-  model$coefficients['X3p1']
  dfch[1, 38] <-  model$coefficients['X3p2']
  dfch[1, 39] <-  model$coefficients['X3p3']
  dfch[1, 40] <-  model$coefficients['X3p4']
  #Y lags
  dfch[1, 41] <-  model$coefficients['Ym2']
  dfch[1, 42] <-  model$coefficients['Ym1']
  
  
  stats <- coef(summary(model))
  
  listad = c("(Intercept)" ,"X1m4" ,"X1m3" ,"X1m2" ,"X1m1" ,"X1" ,"X1p1" ,"X1p2" ,"X1p3" ,"X1p4" ,"X2m4" ,"X2m3", "X2m2" ,"X2m1" ,"X2" ,"X2p1" ,"X2p2" ,"X2p3" ,"X2p4" ,"X3m4" ,"X3m3" ,"X3m2" ,"X3m1" ,"X3" ,"X3p1" ,"X3p2" ,"X3p3" ,"X3p4" ,"Ym2" ,"Ym1")
  

  
  
  #p-value
  informacion <- data.frame("Nombre" = row.names(stats), "Pvalue"=stats[,4])
  informacion <- transform(informacion, indice = match(Nombre,listad))
  
  for (i in 1:length(informacion[,1])){
    indice = informacion[i,3]
    dfch[1, indice + 66] <- informacion[i,2]
  }

  #vif
  vif <-''
  if(length(informacion[,1])<3) {vif <-'NA'} else {
    vif <- t(rbind(car::vif(model)))
  
    informacion1 <-
    data.frame("Nombre" = row.names(vif), "vif" = vif[, 1])
  informacion1 <-
    transform(informacion1, indice1 = match(Nombre, listad))
  
    for (i in 1:length(informacion1[, 1])) {
      indice1 = informacion1[i, 3]
      dfch[1, indice1 + 96] <- informacion1[i, 2]
    }
  }
  
  
  r2 <- ''
  adj.r <- ''
  dfres <- ''
  fstat <- ''
  pvalue <- ''
  durbinwat <- ''
  zeromean <- ''
  anderson <- ''
  breuschpagen <-''
  breuschgodfrey <-''
  nyblom <- ''
  
  
  durbinwat <- lmtest::dwtest(model)$statistic
  zeromean <- t.test(model$residuals)$p.value
  anderson <- nortest::ad.test(model$residuals)$p.value
  breuschpagen <- car::ncvTest(model)$p
  breuschgodfrey <- lmtest::bgtest(model,order=1)$p.value
  nyblom <- strucchange::sctest(model,type='Nyblom-Hansen')$p.value
  
 
  # Parameters
  if (is.null(try(dwtest(model)$statistic,TRUE))) {durbinwat <- 'Null'} else { try(durbinwat <- dwtest(model)$statistic,TRUE)}
  if (is.null(summary(model)$r.squared)) {r2 <- 'Null'} else { r2 <- summary(model)$r.squared}
  if (is.null(summary(model)$adj.r.squared)) {adj.r <- 'Null'} else { adj.r <- summary(model)$adj.r.squared}
  if (is.null(model$df.residual)) {dfres <- 'Null'} else { dfres <- model$df.residual}
  if (is.null(summary(model)$fstatistic)) {fstat <- 'Null'} else { fstat <- summary(model)$fstatistic}
  
  if(max_neg==0 & max_neg1){ pvalue <- 'Null' }   else {  
  if (is.null(pf(fstat[1], fstat[2], fstat[3], lower=FALSE))) {pvalue <- 'Null'} 
  else { pvalue <- pf(fstat[1], fstat[2], fstat[3], lower=FALSE)}
  }  
  
  dfch[1, 43] <- r2
  dfch[1, 44] <- adj.r
  dfch[1, 45] <- dfres
  dfch[1, 46] <- pvalue
  dfch[1, 47] <- durbinwat
  
  dfch[1, 62] <- zeromean
  dfch[1, 63] <- anderson
  dfch[1, 64] <- breuschpagen
  dfch[1, 65] <- breuschgodfrey
  dfch[1, 66] <- nyblom
  #dfch[1, 55] <- vif
  
  if (sum(1 - is.na(dfch[1, 14:22])) == 0) {
    sign_coef_x1 <- ""
    sign_coef_x1_c <- ""
  } else{
    if (sum(dfch[1, 14:22], na.rm = TRUE) >= 0) {
      sign_coef_x1 <- 'Positive'
    } else {
      sign_coef_x1 <- 'Negative'
    }
    if (dfch[1, 5] <= 0 &
        0 <= dfch[1, 6]) {
      sign_coef_x1_c <- sign(dfch[1, 18])
    } else{
      if (0 < dfch[1, 5])        {
        sign_coef_x1_c <- sign(dfch[1, 18 + as.numeric(dfch[1, 5])])
      } else                 {
        sign_coef_x1_c <- sign(dfch[1, 18 + as.numeric(dfch[1, 6])])
      }
    }
    if (sign_coef_x1_c == 1) {
      sign_coef_x1_c <- 'Positive'
    } else {
      sign_coef_x1_c <- 'Negative'
    }
  }
  
  
  #X2
    if (sum(1 - is.na(dfch[1, 23:31])) == 0) {
    sign_coef_x2 <- ""
    sign_coef_x2_c <- ""
  } else{
    if (sum(dfch[1, 23:31], na.rm = TRUE) >= 0) {
      sign_coef_x2 <- 'Positive'
    } else {
      sign_coef_x2 <- 'Negative'
    }
    if (dfch[1, 8] <= 0 &
        0 <= dfch[1, 9]) {
      sign_coef_x2_c <- sign(dfch[1, 27])
    } else{
      if (0 < dfch[1, 8])        {
        sign_coef_x2_c <- sign(dfch[1, 27 + as.numeric(dfch[1, 8])])
      } else                 {
        sign_coef_x2_c <- sign(dfch[1, 27 + as.numeric(dfch[1, 9])])
      }
    }
    if (sign_coef_x2_c == 1) {
      sign_coef_x2_c <- 'Positive'
    } else {
      sign_coef_x2_c <- 'Negative'
    }
  }
  
  
  #X3
  if (sum(1 - is.na(dfch[1, 32:40])) == 0) {
    sign_coef_x3 <- ""
    sign_coef_x3_c <- ""
  } else{
    if (sum(dfch[1, 32:40], na.rm = TRUE) >= 0) {
      sign_coef_x3 <- 'Positive'
    } else {
      sign_coef_x3 <- 'Negative'
    }
    if (dfch[1, 11] <= 0 &
        0 <= dfch[1, 12]) {
      sign_coef_x3_c <- sign(dfch[1, 36])
    } else{
      if (0 < dfch[1, 11])        {
        sign_coef_x3_c <- sign(dfch[1, 36 + as.numeric(dfch[1, 11])])
      } else                 {
        sign_coef_x3_c <- sign(dfch[1, 36 + as.numeric(dfch[1, 12])])
      }
    }
    if (sign_coef_x3_c == 1) {
      sign_coef_x3_c <- 'Positive'
    } else {
      sign_coef_x3_c <- 'Negative'
    }
  }
  
  
  typeofdep <- t10_depvar_list[t10_depvar_list$'Name of the variable'==p10_depvar_list[p10_depvar_list$'Name of the variable'==dfch[1,2],]$'Original variable',]$'Type of variable'
  typeofind_x1 <- p21_indvar_list[p21_indvar_list$'Name.of.the.variable'==dfch[1,4],]$'Type.of.variable'
  typeofind_x2 <- p21_indvar_list[p21_indvar_list$'Name.of.the.variable'==dfch[1,7],]$'Type.of.variable'
  typeofind_x3 <- p21_indvar_list[p21_indvar_list$'Name.of.the.variable'==dfch[1,10],]$'Type.of.variable'
  
  sign_x1 <- signs_table[typeofind_x1,typeofdep]
  sign_x2 <- signs_table[typeofind_x2,typeofdep]
  sign_x3 <- signs_table[typeofind_x3,typeofdep]
  
  if(identical(sign_x1, character(0))){sign_x1 <- 'NaN'}
  if(identical(sign_x2, character(0))){sign_x2 <- 'NaN'}
  if(identical(sign_x3, character(0))){sign_x3 <- 'NaN'}
  
  
  
  dfch[1, 48] <- paste(sign_coef_x1,sign_coef_x1_c,sep = "/")
  dfch[1, 49] <- sign_x1
  dfch[1, 50] <- (sign_coef_x1==sign_x1 & sign_coef_x1_c==sign_x1) | sign_x1 == 'Neutral' | sign_x1 == 'NaN'
  dfch[1, 51] <- paste(sign_coef_x2,sign_coef_x2_c,sep = "/")
  dfch[1, 52] <- sign_x2
  dfch[1, 53] <- (sign_coef_x2==sign_x2 & sign_coef_x2_c==sign_x2) | sign_x2 == 'Neutral' | sign_x2 == 'NaN'
  dfch[1, 54] <- paste(sign_coef_x3,sign_coef_x3_c,sep = "/")
  dfch[1, 55] <- sign_x3
  dfch[1, 56] <- (sign_coef_x3==sign_x3 & sign_coef_x3_c==sign_x3) | sign_x3 == 'Neutral' | sign_x3 == 'NaN'
  

  #check significa que los signos son los correctos, KO no son los correctos. 
  
  if(dfch[1, 50]*dfch[1, 53]*dfch[1, 56]==1){dfch[1, 57] <- 'Check'} else {dfch[1, 57] <- 'KO'}
  k <- length(coefficients(model))
  n <- nobs(model)
  dfch[1, 58] <- AIC(model) + 2*(k*k+k)/(n-k-1)
  #dfch[1, 79] <- lengths(model$model)[1]

  #U(4) Code
  
  # En este punto en el data frame data_lag_tot está la muestra total de observaciones y lags para el actual modelo.
  # Por como está construido, por arriba se pierden algunos leads, y por abajo algunos lags, pero no deber�?a importar porque la 
  # regresión sólo se va a calcular sobre las l�?neas que tengan todos los valores disponibles.
  # De esta muestra total hay que quedarnos sólo con las variables que vamos a utiizar, y sus lags/leads. 
  if (yname=="1"){
    var_tot <- c("Y", xname1, xname2, xname3)  
  }else{
    var_tot <- c("Y", xname1, xname2, xname3, yname)
  }
  var_tot <- var_tot[var_tot!='']   # Remove empties
  var_reg <- c(xname1, xname2, xname3, yname)
  var_reg <- var_reg[var_reg!='']   # Remove empties
  
  three_na_check <- c(xname1, xname2, xname3)
  three_na_check <- three_na_check[three_na_check!='']
  
  #----------------------------------------------Para de correr aqu�?
  if(length(three_na_check)!=0){

    data_lag_tot_cleaned <- data_lag_tot[,colSums(is.na(data_lag_tot)) != nrow(data_lag_tot)]
    data_util <- data_lag_tot_cleaned[complete.cases(data_lag_tot_cleaned),var_tot]
    #data_util <- data_lag_tot[,var_tot]
    #...y con esta quitamos las filas que tengan algún NA
    #data_util <- data_util[complete.cases(data_util),]
    
    # Number of useful data. 
    full_sample_length <- lengths(data_util)[1]
    
    # Number of predictions. 4 = 1 year x 4 quarters
    num_predict <- 4  
    
    # Maximum size of training sample (in-the-sample)
    max_train_sample_length <- full_sample_length - num_predict
    
    # Tamaño m�?nimo de la muestra (cualquier muestra). Viene limitado por el número de variables explicativas. Si el número de 
    # observaciones es menor que el número de variables explicativas nos quedamos sin grados de libertad y la regresión da errores.
    name_pred_variables <- c(xname1, xname2, xname3, yname)
    name_pred_variables <- name_pred_variables[name_pred_variables!='']
    num_pred_variables <- length(name_pred_variables)
    
    min_train_sample_length <- num_pred_variables + 2 # Más dos para tener al menos un grado de libertad.
    
    is_possible <- TRUE
    if(min_train_sample_length>max_train_sample_length){
      is_possible <- FALSE   # Si no hay suficientes observaciones con respecto al número de variables explicativas, se marca como modelo no posible y luego se representa
    }
    
    # Once we know the length of TRAIN y AB, we create the lists with the data. 
    # +----------------------------------+---------+------------------------+----------------+
    # |    Y    |    X1 Lags and Leads   |    ...  |    X1 Lags and Leads   |     Y Lags     |
    # +----------------------------------+---------+------------------------+----------------+
    # |         |                        |         |                        |                |
    # |   T&F   |           T&F          |   T&F   |           T&F          |      T&F       |
    # |         |                        |         |                        |                |
    # +----------------------------------+---------+------------------------+----------------+
    # |    A    |            B           |    B    |            B           |        C       |
    # +----------------------------------+---------+------------------------+----------------+
    # |         |                        |         |                        |                |
    # +----------------------------------+---------+------------------------+----------------+
    #
    # T&F es para pasada, la submuestra que se va a usar para obtener los coeficientes del modelo.
    # B son los valores macroeconónimos que se van a usar para estimar A, con los coeficientes obtenidos de T&F.
    # A son las 12 predicciones que hay que hacer con los coeficientes obtenidos de T&F aplicados sobre los datos de B y C.
    # C son los lags de Y utilizados para estimar A. Estos lags, a partir del primero, son desconocidos (obviamente), y 
    #   deben ser actualizados uno a uno conforme se van calculando las predicciones de A.
    #   NOTA: En una fase preliminar de la herramienta se va a calcular A aplicando los coeficientes a los C conocidos, a modo de aproximación.
    #         Una vez esté hecho as�?, se hará el cálculo más fino, con 12 pasadas, y actualizando C con cada una. <YA ESTÁ HECHO>
    
    # Creamos tres matrices vac�?as del tamaño necesario para ir almacenando en cada pasada A_pred, A_obs y A_naive_pred.
    
    if(is_possible){
       
      A_obs_total <- data.frame(matrix(ncol = 1, nrow = num_predict))
      A_pred_total <- data.frame(matrix(ncol = 1, nrow = num_predict))
     
        i=max_train_sample_length
        t_and_f <- data_util[1:i,]
        AB <- data_util[(i+1):(i+num_predict),]
        B <- data_util[(i+1):(i+num_predict),2:(length(var_tot))]
        A_obs <- data_util[(i+1):(i+num_predict),1]
        
        # Here we obtain the parameters that will be used recursively 12 times
        model <- lm(fmla, data = t_and_f, na.action=na.exclude)
        
        #Stability Coefficients and Statistics
        #B0
        dfch[1, 127] <-  model$coefficients['(Intercept)']
        #X1
        dfch[1, 128] <-  model$coefficients['X1m4']
        dfch[1, 129] <-  model$coefficients['X1m3']
        dfch[1, 130] <-  model$coefficients['X1m2']
        dfch[1, 131] <-  model$coefficients['X1m1']
        dfch[1, 132] <-  model$coefficients['X1']
        dfch[1, 133] <-  model$coefficients['X1p1']
        dfch[1, 134] <-  model$coefficients['X1p2']
        dfch[1, 135] <-  model$coefficients['X1p3']
        dfch[1, 136] <-  model$coefficients['X1p4']
        #X2
        dfch[1, 137] <-  model$coefficients['X2m4']
        dfch[1, 138] <-  model$coefficients['X2m3']
        dfch[1, 139] <-  model$coefficients['X2m2']
        dfch[1, 140] <-  model$coefficients['X2m1']
        dfch[1, 141] <-  model$coefficients['X2']
        dfch[1, 142] <-  model$coefficients['X2p1']
        dfch[1, 143] <-  model$coefficients['X2p2']
        dfch[1, 144] <-  model$coefficients['X2p3']
        dfch[1, 145] <-  model$coefficients['X2p4']
        #X3
        dfch[1, 146] <-  model$coefficients['X3m4']
        dfch[1, 147] <-  model$coefficients['X3m3']
        dfch[1, 148] <-  model$coefficients['X3m2']
        dfch[1, 149] <-  model$coefficients['X3m1']
        dfch[1, 150] <-  model$coefficients['X3']
        dfch[1, 151] <-  model$coefficients['X3p1']
        dfch[1, 152] <-  model$coefficients['X3p2']
        dfch[1, 153] <-  model$coefficients['X3p3']
        dfch[1, 154] <-  model$coefficients['X3p4']
        #Y lags
        dfch[1, 155] <-  model$coefficients['Ym2']
        dfch[1, 156] <-  model$coefficients['Ym1']
        
        
        stats <- coef(summary(model))
        
        listad = c("(Intercept)" ,"X1m4" ,"X1m3" ,"X1m2" ,"X1m1" ,"X1" ,"X1p1" ,"X1p2" ,"X1p3" ,"X1p4" ,"X2m4" ,"X2m3", "X2m2" ,"X2m1" ,"X2" ,"X2p1" ,"X2p2" ,"X2p3" ,"X2p4" ,"X3m4" ,"X3m3" ,"X3m2" ,"X3m1" ,"X3" ,"X3p1" ,"X3p2" ,"X3p3" ,"X3p4" ,"Ym2" ,"Ym1")
        
        #p-value
        informacion <- data.frame("Nombre" = row.names(stats), "Pvalue"=stats[,4])
        informacion <- transform(informacion, indice = match(Nombre,listad))
        
        for (i in 1:length(informacion[,1])){
          indice = informacion[i,3]
          dfch[1, indice + 156] <- informacion[i,2]
        }
        
        r2 <- ''
        adj.r <- ''
        dfres <- ''
        fstat <- ''
        pvalue <- ''
        durbinwat <- ''
        zeromean <- ''
        anderson <- ''
        breuschpagen <-''
        breuschgodfrey <-''
        nyblom <- ''
        
        durbinwat <- lmtest::dwtest(model)$statistic
        zeromean <- t.test(model$residuals)$p.value
        anderson <- nortest::ad.test(model$residuals)$p.value
        breuschpagen <- car::ncvTest(model)$p
        breuschgodfrey <- lmtest::bgtest(model,order=1)$p.value
        nyblom <- strucchange::sctest(model,type='Nyblom-Hansen')$p.value
        
        
        # Parameters
        if (is.null(try(dwtest(model)$statistic,TRUE))) {durbinwat <- 'Null'} else { try(durbinwat <- dwtest(model)$statistic,TRUE)}
        if (is.null(summary(model)$r.squared)) {r2 <- 'Null'} else { r2 <- summary(model)$r.squared}
        if (is.null(summary(model)$adj.r.squared)) {adj.r <- 'Null'} else { adj.r <- summary(model)$adj.r.squared}
        if (is.null(model$df.residual)) {dfres <- 'Null'} else { dfres <- model$df.residual}
        if (is.null(summary(model)$fstatistic)) {fstat <- 'Null'} else { fstat <- summary(model)$fstatistic}
        
        if(max_neg==0 & max_neg1){ pvalue <- 'Null' }   else {  
          if (is.null(pf(fstat[1], fstat[2], fstat[3], lower=FALSE))) {pvalue <- 'Null'} 
          else { pvalue <- pf(fstat[1], fstat[2], fstat[3], lower=FALSE)}
        }  
        
        dfch[1, 187] <- r2
        dfch[1, 188] <- adj.r
        dfch[1, 189] <- dfres
        dfch[1, 190] <- pvalue
        dfch[1, 191] <- durbinwat
        dfch[1, 192] <- zeromean
        dfch[1, 193] <- anderson
        dfch[1, 194] <- breuschpagen
        dfch[1, 195] <- breuschgodfrey
        dfch[1, 196] <- nyblom
        
        #Until here
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        # --- start
        
        first_index <- as.numeric(rownames(t_and_f)[lengths(t_and_f)][1])+1

        current_index <- as.numeric(first_index) # Contador
        #-------- First run:
        A_pred <- predict(model, newdata=AB)
        if('Ym1' %in% yname){AB[rownames(AB)==current_index+1,]$Ym1 <- A_pred[1]}
        if('Ym2' %in% yname){AB[rownames(AB)==current_index+2,]$Ym2 <- A_pred[1]}
        current_index <- current_index + 1

        #-------- Second run:
        A_pred <- predict(model, newdata=AB)
        if('Ym1' %in% yname){AB[rownames(AB)==current_index+1,]$Ym1 <- A_pred[2]}
        if('Ym2' %in% yname){AB[rownames(AB)==current_index+2,]$Ym2 <- A_pred[2]}
        current_index <- current_index + 1
        
        #-------- Third run:
        A_pred <- predict(model, newdata=AB)
        if('Ym1' %in% yname){AB[rownames(AB)==current_index+1,]$Ym1 <- A_pred[3]}
        current_index <- current_index + 1
        
        
        A_pred <- predict(model, newdata=AB)
        
        # --- end
        
        # START ---
        # Se deshacen las transformaciones para calcular la U de Theil sobre las variables originales,
        # y hacer de este modo comparables modelos con distintas transformaciones.

        Y_trans_head_i <- t_and_f$Y
        Y_trans_obs_v <- c(Y_trans_head_i,A_obs)
        Y_trans_pred_vi <- c(Y_trans_head_i,A_pred)
        
        # Hay que encontrar el número máximo de lags y añadirle 4 (en caso de trimestres) o 1 (en caso de anual).
        lag_y <- dfch[1,3]
        if((!is.na(dfch[1,5]) & dfch[1,5]!='NaN')){lag_x1 <- 0-as.numeric(dfch[1,5])} else {lag_x1 <- 0}
        if((!is.na(dfch[1,8]) & dfch[1,8]!='NaN')){lag_x2 <- 0-as.numeric(dfch[1,8])} else {lag_x2 <- 0}
        if((!is.na(dfch[1,11]) & dfch[1,11]!='NaN')){lag_x3 <- 0-as.numeric(dfch[1,11])} else {lag_x3 <- 0}
        
        max_lag <- max(lag_y, lag_x1, lag_x2, lag_x3)
        
        # Get transformation
        # ----------------------
        transfor <- p10_depvar_list[p10_depvar_list$'Name of the variable'==name_d,]$Transformation
        orig_var <- p10_depvar_list[p10_depvar_list$'Name of the variable'==name_d,]$'Original variable'
        orig_var_data <- p10_depvar_data[names(p10_depvar_data)==orig_var]
        first_orig_value <- 0 # Inicializamos la variable
        first_orig_value[1:1] <- orig_var_data[!is.na(orig_var_data)][1:1]
        Y_orig_obs_viii <- orig_var_data[!is.na(orig_var_data)]
        max_lag <- as.numeric(max_lag)
        
        
        if (transfor == 'logit') {
          Y_orig_pred_ix <- plogis(Y_trans_pred_vi)
          
        } else if (transfor == 'logitdif') {
          Y_orig_pred_ix <- plogis(diffinv(Y_trans_pred_vi,xi=qlogis(Y_orig_obs_viii)[(max_lag+1):(max_lag+1)], lag=1))
          cat(paste('_ Check Reverse Transformation ___ \nModel: ',r,'\nSample: ',i,'\nOriginal (',1:3,'): ',Y_orig_obs_viii[2:4] - Y_orig_pred_ix[1:3],'\n',sep=""))
          } 
        
        # After the inverse transformations, the last 12 observations are selected (they will be used for the comparisons.
        
        low_index <- length(Y_orig_obs_viii)-(num_predict-1)-(max_train_sample_length-i)
        
        A_obs_orig <- Y_orig_obs_viii[(length(Y_orig_obs_viii)-(num_predict-1)):length(Y_orig_obs_viii)]
        A_pred_orig <- Y_orig_pred_ix[(length(Y_orig_pred_ix)-(num_predict-1)):length(Y_orig_pred_ix)]
        
        A_obs_total[,1] <- A_obs_orig
        A_pred_total[,1] <- A_pred_orig
        # END ---
      
      
      rmse <- (colMeans((A_obs_total - A_pred_total)^2))^(0.5)
      mae <- colMeans(abs(A_obs_total - A_pred_total))
      mape <- colMeans(abs(A_obs_total - A_pred_total)/abs(A_obs_total))
      
      dfch[1, 59] <- rmse
      dfch[1, 60] <- mae
      dfch[1, 61] <- mape
      #}
      
    } else {

      dfch[1, 59] <- NA
      dfch[1, 60] <- NA
      dfch[1, 61] <- NA
    }
  } else {
    
    dfch[1, 59] <- NA
    dfch[1, 60] <- NA
    dfch[1, 61] <- NA
  }
  dfch
  }

close(pb2)
stopCluster(cluster) 

df<-dfa[,1:196]
#df1<-cbind(dfa[,1:12],dfa[,127:196])



#xl.sheet.activate('SS2.Stability')
#rng = xls[["Activesheet"]]$Cells(2,1)
#xl.write(df1, xl.rng = rng, row.names = FALSE, col.names = TRUE)
           
xl.sheet.activate('SS2.Models')
rng = xls[["Activesheet"]]$Cells(2,1)
xl.write(df, xl.rng = rng, row.names = FALSE, col.names = TRUE)

# Ahora hay que coger de la tabla de modelos generada, para cada combinación de variables, la combinación de lags que tenga el top menor AIC y cuyas variables principales tengan
# p-valor menor al valor indicado
# Candidate Models. A2.
setWinProgressBar(pb, 95, label='Selecting Better Combination') 
df_best <- data.frame(matrix(ncol = 196, nrow = nrow(p30_models_list)))

for (i in 1:lengths(p30_models_list)[1]){ #i=1
  vd <- p30_models_list[i,]$Var1
  v1 <- p30_models_list[i,]$Var2
  v2 <- p30_models_list[i,]$Var3
  v3 <- p30_models_list[i,]$Var4
  
  mod_combs <- df[df$X2==vd & df$X4==v1 & df$X7==v2 & df$X10==v3 & df$X57=='Check',]
  
  if (max(is.na(mod_combs$X72))==1){
    mod_combs[is.na(mod_combs$X72),]$X72 <- 0
    mod_combs<- mod_combs[mod_combs$X72<=pvalfilter,]
    mod_combs[mod_combs$X72==0,]$X72 <- NA
  }else{
    mod_combs<- mod_combs[mod_combs$X72<=pvalfilter,]
  }
  if (max(is.na(mod_combs$X81))==1){
    mod_combs[is.na(mod_combs$X81),]$X81 <- 0
    mod_combs<- mod_combs[mod_combs$X81<=pvalfilter,]
    mod_combs[mod_combs$X81==0,]$X81 <- NA
  }else{
    mod_combs<- mod_combs[mod_combs$X81<=pvalfilter,]
  }
  if (max(is.na(mod_combs$X90))==1){
    mod_combs[is.na(mod_combs$X90),]$X90 <- 0
    mod_combs<- mod_combs[mod_combs$X90<=pvalfilter,]
    mod_combs[mod_combs$X90==0,]$X90 <- NA
  }else{
    mod_combs<- mod_combs[mod_combs$X90<=pvalfilter,]
  }
  
  mod_combs<- mod_combs[mod_combs$X43>=Rsquaredfilter,]
  mod_combs$X46 <- as.double(mod_combs$X46)
  mod_combs<- mod_combs[mod_combs$X46<=pvalFfilter,]
  
  mod_combs$X62 <- as.double(mod_combs$X62)
  mod_combs<- mod_combs[mod_combs$X62>=zerofilter,]
  mod_combs$X63 <- as.double(mod_combs$X63)
  mod_combs<- mod_combs[mod_combs$X63>=AndDarlingfilter,]
  mod_combs$X64 <- as.double(mod_combs$X64)
  mod_combs<- mod_combs[mod_combs$X64>=BrPagenfilter,]
  mod_combs$X65 <- as.double(mod_combs$X65)
  mod_combs<- mod_combs[mod_combs$X65>=BrGodfreyfilter,]
  mod_combs$X66 <- as.double(mod_combs$X66)
  mod_combs<- mod_combs[mod_combs$X66>=NybHansenfilter,]

  
  best_comb <- mod_combs[order(mod_combs$X58),][1:AICfilter,]
  df_best <- rbind(df_best,best_comb)
}

df_best<-df_best[!is.na(df_best$X2),]

setWinProgressBar(pb, 100, label='Writing Outputs') 

xl.sheet.activate('S2.Models')
rng = xls[["Activesheet"]]$Cells(2,1)
xl.write(df_best, xl.rng = rng, row.names = FALSE, col.names = TRUE)
#df_best$X1 <- as.integer(df_best$X1)
#xl.write(df_best[,-1], xl.rng = rng, row.names = TRUE, col.names = TRUE)
#xl.write('X1', xl.rng = rng, row.names = FALSE, col.names = FALSE)

close(pb)