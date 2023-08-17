import json
from bs4 import BeautifulSoup
import csv
import pandas as pd
import warnings
import requests
from decouple import config
import fileinput
import csv
import re
warnings.filterwarnings('ignore')

tipo = config('TIPO')
login = config('LOGIN')
senha = config('SENHA')

if (tipo == "prd"):
    baseUrl = 'https://totvssign.totvs.app/'
else:
    baseUrl = 'https://totvssign.staging.totvs.app/'
# ------------------------------------------------------------------
def replace_in_file(file_path, search_text, new_text):
    with fileinput.input(file_path, inplace=True) as file:
        for line in file:
            new_line = line.replace(search_text, new_text)
            print(new_line, end='')
# ------------------------------------------------------------------
def gerarToken(token):
    req = {}
    req = {
        'url': baseUrl+'identityintegration/api/auth/login',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json"
        },
        'json': {"userName": login, "password": senha},
        'verify':False
    }
    rLogin = json.loads((requests.post(**req)).text)
    if (rLogin['succeeded']):
        print("gerarToken(): "+str(rLogin['succeeded']))
        replace_in_file('.env','TOKEN='+token,'TOKEN='+rLogin['data']['token'])
        token = rLogin['data']['token']
        return token
    else:
        print("ERRO TOKEN")
        print(rLogin['description'])
        exit()
# ------------------------------------------------------------------
def recuperarDocUnico(idTAE):
    if not (idTAE): idTAE='1679838'
    req = {}
    req = {
        'url': baseUrl+'documents/v1/publicacoes/'+idTAE,
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+token
        },
        'verify':False
    }

    rreq = requests.get(**req)
    if(rreq.status_code==401):
        ntoken = gerarToken(token)
        req['headers']['authorization'] = "Bearer "+ntoken
        rreq = requests.get(**req)

    rReq = json.loads((rreq).text)
    if(rReq['success']):
        print("recuperarDocUnico(): "+str(rReq['success']))
        print(rReq['data'])
        # print('ID: '+str(rReq['data']['id'])+' - TM: '+str(rReq['data']['tamanhoArquivo']))

    else:
        print('ERRO BUSCAR PUBLICACAO')
        print(str(rReq['errors'])+':'+str(rReq['code']))
        exit()
# ------------------------------------------------------------------
def recuperarListaUsuarios():
    req = {}
    req = {
        'url': baseUrl+'identityintegration/v1/administrators/user-list?PaginaAtual=1',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+token
        },
        'verify':False
    }
    rrre=requests.get(**req)
    if(rrre.status_code==401):
        ntoken = gerarToken(token)
        req['headers']['authorization'] = "Bearer "+ntoken
        rrre = requests.get(**req)

    rrReq = json.loads((rrre).text)
    if(rrReq['succeeded']):
        print("recuperarListaUsuarios(): "+str(rrReq['succeeded']))
        return rrReq
        # print(rrReq['data'])
        # print('ID: '+str(rReq['data']['id'])+' - TM: '+str(rReq['data']['tamanhoArquivo']))

    else:
        print('ERRO BUSCAR PUBLICACAO')
        print(str(rrReq['errors'])+':'+str(rrReq['code']))
        exit()
# ------------------------------------------------------------------
def recuperarDocLista(token):
    req = {}
    req = {
        'url': baseUrl+'documents/v1/publicacoes/pesquisas?PaginaAtual=1&TamanhoPagina=500000',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+token
        },
        'json': {
            "pesquisarEmTodaEmpresa": True
        },
        'verify':False
    }

    reqDocs = requests.post(**req)
    if(reqDocs.status_code==401):
        ntoken = gerarToken(token)
        req['headers']['authorization'] = "Bearer "+ntoken
        reqDocs = requests.post(**req)

    if (reqDocs.status_code == requests.codes.ok):
        r = json.loads(reqDocs.text)
    else:
        print(reqDocs.raise_for_status)
        print('Erro!')
        exit()
# ------------------------------------------------------------------
def dadosUsuario(usuario,emailCheck,cpfCheck):
    listaUsuarios=[]
    with open('usuariosSS.csv', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            if (usuario):
                if (usuario!=(row['Email'].lower()) and usuario!=(row['cpf'].replace('.','').replace('-',''))):
                    continue
            
            if (row['Email'].lower()!=emailCheck):
                print('>>EMAIL INVALIDO: '+usuario)
                return []
            if (row['cpf'].replace('.','').replace('-','')!=cpfCheck):
                print('>>CPF INVALIDO: '+usuario)
                return []
                
            cargoOld=row['cargo'].replace(' (A)','').strip()
            unidadeOld = row['unidade'].replace(" ","")
            un = unidadeOld.split('-')
            if (len(un)==2):
                nUn = un[1].replace("Nº","").replace("nº","")
            elif(len(un)==3):
                nUn = un[1]+un[2].replace("Nº","").replace("nº","")
                if(len(nUn)<=5):
                    nUn="Unidade"+nUn
            elif(len(un)==4):
                nUn = un[2]+un[3].replace("Nº","").replace("nº","")
            else:
                nUn = "DEX"
            row['unidade'] = nUn
            row['cargo'] = cargoOld
            row['CargoUnidade'] = cargoOld + " (" + nUn + ")"
            listaUsuarios.append(row)
        
    
    return listaUsuarios
# ------------------------------------------------------------------
def outros(rReq2,atualizaCargo,grupo,filtroUsuarioEmail):
    if not(rReq2):
        f = open('usuariosTAE.json')
        arqAssin = json.load(f)
        f.close()
    else:
        arqAssin = rReq2
    
    usuariosUnidade = []
    cargosLista = []
    cargosExcluidos=[]
    cargosExcluidos2=[]
    cont=0
    for i in arqAssin['data']['registro']:
        vPosition = i['position']

        if (filtroUsuarioEmail):
            if (i['userName']==filtroUsuarioEmail):
                print(i)
            continue

        if len(i['cpf'])!=11:
            cont+=1
        if vPosition=='' or vPosition==None:
            vPosition='SEM CARGO'
        
        fn = i['phoneNumber'] if i['phoneNumber']!=None else ''
        userName = i['userName']
        validEmail= i['userName']
        if ("@itl.org.br" in userName):
            userName=i['cpf']
            validEmail=validEmail.replace('@itl.org.br','@sestsenat.org.br')

        if (atualizaCargo):
            du=dadosUsuario(userName,validEmail,i['cpf'])
            if (len(du)>0):
                UArq=du[0]['unidade']
                CUArq=du[0]['CargoUnidade']
                CArq=du[0]['cargo']
                edit=False

                
                if((UArq=="DEX" or CArq=='DIRETOR DE UNIDADE' or CArq=='COORDENADOR DE ADMINISTRACAO E FINANCAS' or CArq=='COORDENADOR DE DESENVOLVIMENTO PROFISSIONAL' or CArq=='COORDENADOR DE PROMOCAO SOCIAL') and i['isPublisher']==False):
                    print(UArq + ' ' + CArq)
                    i['isPublisher']=True
                    edit=True
                if(vPosition!=CUArq or edit):
                    i['position'] = CUArq
                    req = {}
                    req = {
                        'url': baseUrl+'identityintegration/v1/administrators/user',
                        'headers': {
                            "accept": "application/json",
                            "content-type": "application/json",
                            "authorization": "Bearer "+token
                        },
                        'verify':False,
                        'json':{
                            "id":i['id'],
                            "fullName": i['fullName'],
                            "phoneNumber":fn,
                            "position": CUArq,
                            "isPublisher":i['isPublisher'],
                            "isAdministrator":i["isAdministrator"]
                        }
                    }
                    rreq = requests.put(**req)
                    if(rreq.status_code==401):
                        ntoken = gerarToken(token)
                        req['headers']['authorization'] = "Bearer "+ntoken
                        rreq = requests.get(**req)

                    rReq = json.loads((rreq).text)
                    if(rReq['succeeded']):
                        print(i['userName']+' : '+rReq['description'])
            else:
                print('USUARIO NÃO LOCALIZADO: '+i['email']+' '+i['cpf']+' '+i['fullName'])
        
        reg = r'\([\s\S]*\)'
        cargo2 = re.sub(reg, '', i['position'])
        if (cargo2 not in cargosLista):
            cargosLista.append(cargo2)

        if ('Unidade' in vPosition):
            vPos=vPosition.split('Unidade')[1].replace(' ','').replace(')','')
            usuariosUnidade.append({'email':i['userName'],'localizacao':vPos})
            if ("D62" in vPosition):
                continue
        elif('DEX' in vPosition):
            if (grupo):
                usuariosUnidade.append({'email':i['userName'],'localizacao':vPosition})
                # usuariosUnidade.append(i['userName'])
            continue
        else:
            continue
    
    if (filtroUsuarioEmail):
        usuariosUnidade.append({'email':filtroUsuarioEmail,'localizacao':''})

    totalArquivos = 0
    totalAssinaturas = 0
    usuarioComMaisUsoDocumento = ''
    usuarioComMaisUsoAssinatura = ''
    valorMaisAltoDocumento = 0
    qtdAssinaturaUsuarioDocumento = 0
    qtdAssinaturaUsuarioAssinatura = 0
        
    data2 = pd.DataFrame(pd.read_excel('TAE.xlsx'), columns=['AUTOR', 'ID.','DESTINATÁRIO','HASH'])
    hashAnterior=0

    teste = []

    for i, value in enumerate(usuariosUnidade):
        enviosAutor = data2[data2["AUTOR"] == value['email']]
        tempDocs=0
        tempAss=0

        if (enviosAutor.index.empty):
            continue

        for i,hashAtual in enumerate(enviosAutor["HASH"]):
            tempAss+=1
            totalAssinaturas+=1
            if (hashAtual!=hashAnterior):
                tempDocs+=1
                totalArquivos+=1
            
            hashAnterior=hashAtual
        
        if (tempDocs>valorMaisAltoDocumento):
           valorMaisAltoDocumento=tempDocs
           usuarioComMaisUsoDocumento=value['email']
           qtdAssinaturaUsuarioDocumento=tempAss
        if (tempAss>qtdAssinaturaUsuarioAssinatura):
           usuarioComMaisUsoAssinatura=value['email']
           qtdAssinaturaUsuarioAssinatura=tempAss
        
        
        
        for indice,valor in enumerate(teste):
            valid=False
            if(valor['unidade']==value['localizacao']):
                valor['usuarios'].append(value['email'])
                valor['envios']=(valor['envios']+tempAss)
                valid=True

            if (indice+1==len(teste) and not valid):
                teste.append({
                    'unidade':value['localizacao'],
                    'usuarios':[value['email']],
                    'envios':tempAss
                })
                break
        
        if (len(teste)==0):
            teste.append({
                'unidade':value['localizacao'],
                'usuarios':[value['email']],
                'envios':tempAss
            })

        
       
        # print(value['email'] + " " + str(tempDocs) + " " + str(tempAss) + " "+ value['localizacao'])
    # print(teste)
    print("Total de Arquivos: "+str(totalArquivos))
    print("Total de Assinaturas: "+str(totalAssinaturas))
    print("Usuário com mais envio de documentos: "+usuarioComMaisUsoDocumento)
    print("Qtd de documentos do usuário: "+str(valorMaisAltoDocumento))
    print("Qtd de assinaturas do usuário: "+str(qtdAssinaturaUsuarioDocumento))
    print("Usuário com mais assinaturas: "+usuarioComMaisUsoAssinatura)
    print("Qtd de assinaturas do usuário: "+str(qtdAssinaturaUsuarioAssinatura))
    print("Qtd usuários selecionados: "+str(len(usuariosUnidade)))

token = config('TOKEN')
atualizaCargo = True
recuperarTodos = False
filtroUsuarioEmail=''
if not (token): gerarToken(token)
# recuperarDocUnico(id)
# recuperarDocLista(token)
rReq2=[]
rReq2=recuperarListaUsuarios()
outros(rReq2,atualizaCargo,recuperarTodos,filtroUsuarioEmail)
