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
        print("recuperarListaUsuarios(): "+str(rrReq['succeeded'])+str(len(rrReq['data']['registro'])))
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

    if (cpfCheck=='67611150600'):
        return []
    with open('usuariosSS.csv', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            emailCorreto=row['Email'].lower()
            if (usuario):
                # if ("@itl.org.br" in usuario):
                    # emailCorreto=emailCorreto.replace('@sestsenat.org.br','@itl.org.br')
                if (usuario!=emailCorreto and usuario!=(row['cpf'].replace('.','').replace('-',''))):
                    continue
            
            if (emailCorreto!=emailCheck):
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
            if (i['userName']=='ponto.dn128@sestsenat.org.br' or i['userName']=='pontoeletronico@sestsenat.org.br'):
                    print("EMAIL PADRÂO: "+i['userName']+" "+str(i['cpf']))
            else:
                print("CPF INVALIDO "+i['userName'])
            continue
        if vPosition=='' or vPosition==None:
            vPosition='SEM CARGO'
        
        fn = i['phoneNumber'] if i['phoneNumber']!=None else ''
        userName = i['userName']
        validEmail= i['userName']

        if (atualizaCargo):
            du=dadosUsuario(userName,validEmail,i['cpf'])
            if (len(du)>0):
                UArq=du[0]['unidade']
                CUArq=du[0]['CargoUnidade']
                CArq=du[0]['cargo'].replace(" II","").replace(" I","")

                siglaUnidade=''
                edit=False
                
                if (UArq!='DEX'):
                    siglaUnidade=UArq.replace("Unidade","")[0]
                    # print(CArq)
                    # print(siglaUnidade)
                
                usuariosLiberados=[
                    'joicepadilha@sestsenat.org.br',
                    'alexandrapereira@sestsenat.org.br',
                    'marianascimento@sestsenat.org.br',
                    'josianefarias@sestsenat.org.br',
                    'pollyanalazzarin@sestsenat.org.br',
                    'jacquelinesantos@sestsenat.org.br',
                    'luizmarcos@sestsenat.org.br',
                    'cylmarabrito@sestsenat.org.br',
                    'chaianabrustolin@sestsenat.org.br',
                    'gleisonsilva@sestsenat.org.br',
                    'priscilacosta@sestsenat.org.br',
                    'daianawalter@sestsenat.org.br',
                    'mariliaschneider@sestsenat.org.br',
                    'katiaramos@sestsenat.org.br',
                    'alexandrecarmo@sestsenat.org.br',
                    'janeassis@sestsenat.org.br',
                    'amandacavalcanti@sestsenat.org.br'
                ]

                usuariosSemCargoLiberado=[
                    'anaduque@sestsenat.org.br',
                    'andrezanola@sestsenat.org.br',
                    'claudiocabral@sestsenat.org.br',
                    'nadiescasouza@sestsenat.org.br',
                    'renatomacedo@sestsenat.org.br'
                ]

                if (userName in usuariosSemCargoLiberado):
                    CArq="DIRETOR DE UNIDADE"
                    CUArq=CArq+" ("+UArq+")" 

               
                if(UArq=="DEX" or CArq=='DIRETOR DE UNIDADE' or CArq=='COORDENADOR DE ADMINISTRACAO E FINANCAS' or CArq=='COORDENADOR DE DESENVOLVIMENTO PROFISSIONAL' or CArq=='COORDENADOR DE PROMOCAO SOCIAL' or CArq=='GERENTE DE UNIDADE'):
                    if(i['isPublisher']==False):
                        print(UArq + ' ' + CArq)
                        i['isPublisher']=True
                        edit=True
                elif("TECNICO" in CArq):
                    if (siglaUnidade=="D" and i['isPublisher']==False):
                        print(CArq + " - "+siglaUnidade)
                        i['isPublisher']=True
                        edit=True
                elif(i['userName'] in usuariosLiberados):
                    if(i['isPublisher']==False):
                        i['isPublisher']=True
                        edit=True
                elif(CArq=='CARGO'):
                    if (i['lockoutEnabled']==False):
                        print("> "+ userName)
                        i['lockoutEnabled']=True
                        edit=True
                else:
                    if(i['isPublisher']==True):
                        i['isPublisher']=False
                        edit=True
                        print(">>> "+siglaUnidade+" - "+CArq)

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
                            "isAdministrator":i["isAdministrator"],
                            "isDisabled":i['lockoutEnabled']
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
                if (i['cpf']=='67611150600'):
                    print('Não atualizar: '+i['email']+' '+i['cpf']+' '+i['fullName'])
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
                # print(str(indice) + ' ' + value['localizacao'] + '---')
                # print(valor['envios'])
                # print(tempAss)
                # print(value['email'])
                valor['usuarios'].append(value['email'])
                valor['envios']=(valor['envios']+tempAss)
                valid=True
                break

            if (indice+1==len(teste) and not valid):
                # print(str(indice) + ' ' + value['localizacao'])
                teste.append({
                    'unidade':value['localizacao'],
                    'usuarios':[value['email']],
                    'envios':tempAss
                })
                # print(value['email'])
                break
        
        if (len(teste)==0):
            teste.append({
                'unidade':value['localizacao'],
                'usuarios':[value['email']],
                'envios':tempAss
            })

        
       
        # print(value['email'] + " " + str(tempDocs) + " " + str(tempAss) + " "+ value['localizacao'])
    def myFunc(e):
        return e['unidade']
    teste.sort(key=myFunc)

    # for xx in teste:
        # if (xx['unidade']=='B73'):
            # print(xx['envios'])
    teste1 = json.dumps(teste)
    dff = pd.read_json(teste1)
    dff.to_csv('file.csv')
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
