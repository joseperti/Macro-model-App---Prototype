# Test Suite for SQL Alchemy

from sqlalchemy import create_engine
import pandas as pd
engine = create_engine('mysql+pymysql://epz3ofwjth0uo2nj:zmxob5delcmghi3g@j1r4n2ztuwm0bhh5.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/rnqd4v5frbs2v9rn')
with engine.connect() as conn:
     #resultados1 = conn.execute("select * from tablaModelos")
     #print(resultados1.fetchall())
     schema = ""
     queryPostgreSQL = 'select distinct `First Group`, `Second Group`, `Third Group`, Portfolio from tablaModelos'
     output1 = pd.read_sql(queryPostgreSQL,conn)
     print(output1)
     #schema = "macromodelschema."
     #queryPostgreSQL = 'select distinct "First Group", "Second Group", "Third Group", Portfolio from %stablaModelos' %(schema)
     #resultados = conn.execute(queryPostgreSQL)
     #print(resultados.fetchall())
     #schema = "macromodelschema."
     #output1 = pd.read_sql("delete from %stablaModelos where masterkey = 'Nada'" %(schema),conn)
     #print(output1) 

#conn = engine.connect()
#conn.execute('Insert into macromodelschema.tablaModelos ("First Group", "Second Group", "Third Group") values (NULL,NULL,NULL)')
