"""
    high level support for doing this and that.
"""
import json
import csv
import re
import fileinput
from time import sleep
import warnings
from numpy import tri
import pandas as pd
import requests
from decouple import config
from datetime import date
from requests.exceptions import RequestException
import os

warnings.filterwarnings('ignore')

tipo = config('TIPO')
login = config('LOGIN')
senha = config('SENHA')
token = ''

if tipo == "prd":

    BASE_URL = 'https://totvssign.totvs.app/'
else:
    BASE_URL = 'https://totvssign.staging.totvs.app/'
# ------------------------------------------------------------------
def replace_in_file(file_path, search_text, new_text):
    print('replace_in_file()')
    """Function printing python version."""
    with fileinput.input(file_path, inplace=True) as file:
        for line in file:
            new_line = line.replace(search_text, new_text)
            print(new_line, end='')
# ------------------------------------------------------------------
def atualizaUsuario(i,CUArq,BASE_URL,fn):
    """Function printing python version."""
    i['position'] = CUArq
    req = {}
    req = {
        'url': BASE_URL+'identityintegration/v1/administrators/user',
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
    try:
        rreq = requests.put(**req,timeout=500)
        if(rreq.status_code==401):
            req['headers']['authorization'] = "Bearer "+gerarToken()
            rreq = requests.get(**req,timeout=500)
        rReq = json.loads((rreq).text)
        if(rReq['succeeded']):
            print(i['userName']+' : '+rReq['description'])

        return i
    except RequestException as e:
        print(e)
        print('sleeping......')
        sleep(20)
        print('wake up......')
        rreq = requests.put(**req,timeout=500)
        if(rreq.status_code==401):
            req['headers']['authorization'] = "Bearer "+gerarToken()
            rreq = requests.get(**req,timeout=500)
        rReq = json.loads((rreq).text)
        if(rReq['succeeded']):
            print(i['userName']+' : '+rReq['description'])
        return i
    
    except:
        exit()
        

def gerarToken():
    """Function printing python version."""
    req = {}
    req = {
        'url': BASE_URL+'identityintegration/api/auth/login',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json"
        },
        'json': {"userName": login, "password": senha},
        'verify':False
    }
    rLogin = json.loads((requests.post(**req)).text)
    if rLogin['succeeded']:
        print("gerarToken(): "+str(rLogin['succeeded']))
        # replace_in_file('.env','TOKEN='+token,'TOKEN='+rLogin['data']['token'])
        token = rLogin['data']['token']
        # os.environ['TOKEN'] =rLogin['data']['token']
        return token
    else:
        print("ERRO TOKEN")
        print(rLogin['description'])
        exit()
# ------------------------------------------------------------------
def recuperarDocUnico(idTAE):
    """Function printing python version."""
    if not (idTAE): idTAE='1679838'
    req = {}
    req = {
        'url': BASE_URL+'documents/v1/publicacoes/'+idTAE,
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+token
        },
        'verify':False
    }

    rreq = requests.get(**req)
    if(rreq.status_code==401):
        req['headers']['authorization'] = "Bearer "+gerarToken()
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
    print('recuperarListaUsuarios()')
    """Function printing python version."""
    req = {}
    req = {
        'url': BASE_URL+'identityintegration/v1/administrators/user-list?PaginaAtual=1',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+token
        },
        'verify':False
    }
    
    rrre=requests.get(**req)
    if (rrre.content==b''):
        print("erro ao consultar")
        exit()
    if(rrre.status_code==401):
        req['headers']['authorization'] = "Bearer "+gerarToken()
        rrre = requests.get(**req)

    rrReq = json.loads((rrre).text)
    if(rrReq['succeeded']):
        with open('usuariosTAE.json', 'w', encoding='utf-8') as f:
            json.dump(rrReq, f, ensure_ascii=False, indent=4)
        print("recuperarListaUsuarios(): "+str(rrReq['succeeded'])+str(len(rrReq['data']['registro'])))
        return rrReq
        # print(rrReq['data'])
        # print('ID: '+str(rReq['data']['id'])+' - TM: '+str(rReq['data']['tamanhoArquivo']))

    else:
        print('ERRO BUSCAR PUBLICACAO')
        print(str(rrReq['errors'])+':'+str(rrReq['code']))
        exit()
# ------------------------------------------------------------------
def recuperarDocLista():
    """Function printing python version."""
    req = {}
    req = {
        'url': BASE_URL+'documents/v1/publicacoes/pesquisas?PaginaAtual=1&TamanhoPagina=0',
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
    if reqDocs.status_code==401:
        req['headers']['authorization'] = "Bearer "+gerarToken()
        reqDocs = requests.post(**req)

    
    if reqDocs.status_code == requests.codes['ok']:
        r = json.loads(reqDocs.text)
        print(r)
    else:
        print(reqDocs.raise_for_status)
        print('Erro!')
        exit()
# ------------------------------------------------------------------
def dadosUsuario(usuario,emailCheck,cpfCheck):
    """Function printing python version."""
    listaUsuarios=[]

    if cpfCheck=='67611150600':
        return []
    info='usuario,cpf,Nome,unidade,cargo,Email\n'
    atualizar=False
    Lines = open('usuariosSS.csv', 'r',encoding='utf-8-sig').readlines()
    for linex in Lines:
        if not (info in linex):
            atualizar=True
        break

    if atualizar:
        with open('usuariosSS.csv', 'r+',newline='',encoding='utf-8-sig') as file: 
            file_data = file.read().replace(';',',')
            file.seek(0)
            file.write(info + file_data)
            file.close()
            
    with open('usuariosSS.csv', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            emailCorreto=row['Email'].lower()
            if usuario:
                # if "@itl.org.br" in usuario:
                    # emailCorreto=emailCorreto.replace('@sestsenat.org.br','@itl.org.br')
                if usuario!=emailCorreto and usuario!=(row['cpf'].replace('.','').replace('-','')):
                    continue

            if emailCorreto!=emailCheck:
                print('>>EMAIL INVALIDO: '+usuario)
                return []
            if row['cpf'].replace('.','').replace('-','')!=cpfCheck:
                print('>>CPF INVALIDO: '+row['cpf']+">"+cpfCheck+" "+usuario)
                return []

            cargoOld=row['cargo'].replace(' (A)','').strip()
            unidadeOld = row['unidade'].replace(" ","")
            un = unidadeOld.split('-')
            
            if(un[len(un)-1]=='SENAT'):
                del un[len(un)-1]
            
            if len(un)==2:
                nUn = un[1].replace("Nº","").replace("nº","").replace("n°","").replace("N°","")
            elif len(un)==3:
                nUn = (un[1]+un[2]).replace("Nº","").replace("nº","").replace("n°","").replace("N°","")
                if len(nUn)<=5:
                    nUn="Unidade"+nUn
            elif len(un)==4:
                nUn = (un[2]+un[3]).replace("Nº","").replace("nº","").replace("n°","").replace("N°","")
            else:
                nUn = "DEX"
            row['unidade'] = nUn
            row['cargo'] = cargoOld
            row['CargoUnidade'] = cargoOld + " (" + nUn + ")"
            listaUsuarios.append(row)


    return listaUsuarios
# ------------------------------------------------------------------
def outros(atualizaListaUsuarios,atualizaCargo,grupo,filtroUsuarioEmail,recuperaDocs, recuperaDoc):
    """Function printing python version."""
    
    if not (token): token=gerarToken() #Gera token de autenticação TAE
    
    if recuperaDocs:
        recuperarDocLista()
    
    if recuperaDoc:
        recuperarDocUnico(id)
    
    rReq2=[]
    if (atualizaListaUsuarios):
        rReq2=recuperarListaUsuarios()
    
    if not(rReq2):
        print("Carregando Arquivo")
        f = open('usuariosTAE.json')
        arqAssin = json.load(f)
        f.close()
    else:
        print("Abrindo usuários Online")
        arqAssin = rReq2

    usuariosUnidade = []
    cargosLista = []
    file1 = open("myfile.txt", "a")  # append mode
    file1.write("\n\n"+(date.today()).strftime("%d/%m/%Y")+"\n")
    file1.close()
    for i in arqAssin['data']['registro']:
        vPosition = i['position']

        if filtroUsuarioEmail:
            if i['userName']==filtroUsuarioEmail:
                print(i)
            else:
                continue

        if len(i['cpf'])!=11:
            if i['userName']=='ponto.dn128@sestsenat.org.br' or i['userName']=='pontoeletronico@sestsenat.org.br':
                usuariosUnidade.append({'email':i['userName'],'localizacao':'PONTO'})
                if (filtroUsuarioEmail):
                    break
            else:
                if (i['userName']=='evandrooliveira@sestsenat.org.br' or 
                    i['userName']=='liviaspadoni@sestsenat.org.br' or
                    i['userName']=='lauragrandizoli@sestsenat.org.br'):
                    print("DESABILITANDO>>>>")
                    if not (i['lockoutEnabled']):
                        i['lockoutEnabled']=True
                        atualizaUsuario(i,i['position'],BASE_URL,fn)
                    continue
                print("CPF INVALIDO "+i['cpf']+">>>"+i['userName'])
                file1 = open("myfile.txt", "a")  # append mode
                file1.write(i['userName']+"\n")
                file1.close()
            continue
        
        if not atualizaCargo and i['lockoutEnabled']:
            continue

        if i['userName']=='ponto.a001@sestsenat.org.br':
            continue

        if vPosition=='' or vPosition==None:
            vPosition='SEM CARGO'
            
        fn = i['phoneNumber'] if i['phoneNumber']!=None else ''
        userName = i['userName']
        validEmail= i['userName']
        
        if atualizaCargo:
            if validEmail=='renatocarvalho2@sestsenat.org.br' or userName=='renatocarvalho2@sestsenat.org.br':
                validEmail='renatocarvalho@sestsenat.org.br'
                userName='renatocarvalho@sestsenat.org.br'

            if validEmail=='nadiescasouza@sestsenat.org.br' or userName=='nadiescasouza@sestsenat.org.br':
                validEmail='nadiescaazeredo@sestsenat.org.br'
                userName='nadiescaazeredo@sestsenat.org.br'
                
            du=dadosUsuario(userName,validEmail,i['cpf'])
            if validEmail=='renatacarvalhooliveira@sestsenat.org.br':
                du.append({
                    'usuario': 'renatacarvalhooliveira', 
                    'cpf': '035.816.697-73', 
                    'Nome': 'Renata Carvalho de Oliveira', 
                    'unidade': 'UnidadeB56', 
                    'cargo': 'ODONTOLOGO (A)', 
                    'Email': 'renatacarvalhooliveira@sestsenat.org.br', 
                    'CargoUnidade': 'ODONTOLOGO (UnidadeB56)'})
                
            if len(du)>0:
                UArq=du[0]['unidade']
                CUArq=du[0]['CargoUnidade']
                CArq=du[0]['cargo'].replace(" II","").replace(" I","")

                siglaUnidade=''
                edit=False
                paramEdit=''
                # i['isPublisher']=True

                if UArq!='DEX':
                    siglaUnidade=UArq.replace("Unidade","")[0]
                    # print(CArq)
                    # print(siglaUnidade)

                usuariosLiberados = json.load(open('usuariosLiberados.json'))

                usuariosSemCargoLiberado=[
                    'anaduque@sestsenat.org.br',
                    'andrezanola@sestsenat.org.br',
                    'claudiocabral@sestsenat.org.br',
                    'nadiescasouza@sestsenat.org.br',
                    'renatomacedo@sestsenat.org.br',
                ]

                if userName in usuariosSemCargoLiberado:
                    CArq="DIRETOR DE UNIDADE"
                    CUArq=CArq+" ("+UArq+")"


                if (UArq=="DEX"
                    or CArq=='DIRETOR DE UNIDADE'
                    or CArq=='COORDENADOR DE ADMINISTRACAO E FINANCAS'
                    or CArq=='COORDENADOR DE DESENVOLVIMENTO PROFISSIONAL'
                    or CArq=='COORDENADOR DE PROMOCAO SOCIAL'
                    or CArq=='GERENTE DE UNIDADE'):
                    if not i['isPublisher']:
                        print(UArq + ' ' + CArq)
                        i['isPublisher']=True
                        edit=True
                        paramEdit=paramEdit+'/PUBLICADOR-DIRETOR/'
                    
                elif "TECNICO" in CArq:
                    if siglaUnidade=="D" and not i['isPublisher']:
                        print(CArq + " - "+siglaUnidade)
                        i['isPublisher']=True
                        edit=True
                        paramEdit=paramEdit+'/PUBLICADOR-TECNICO-D/'
                elif i['userName'] in usuariosLiberados:
                    if not i['isPublisher']:
                        i['isPublisher']=True
                        edit=True
                        paramEdit=paramEdit+'/USUARIO-HABILITADO/'
                elif CArq=='CARGO':
                    if i['lockoutEnabled']:
                        print(">-- SEM CARGO:  "+ userName)
                        i['lockoutEnabled']=False
                        edit=True
                        paramEdit=paramEdit+'/CARGO/'
                else:
                    if i['isPublisher']:
                        i['isPublisher']=False
                        edit=True
                        paramEdit=paramEdit+'/DESABILITAR-PUBLICADOR/'
                        # print(">>> "+siglaUnidade+" - "+CArq)
                
                if i['lockoutEnabled']:
                    i['lockoutEnabled']=False
                    edit=True
                    paramEdit=paramEdit+'/DESATIVADO-TRUE/'
                    

                if(vPosition!=CUArq or edit):
                    # if not (edit):
                        # print("/NOME-CARGO/")
                    # else:
                        # print(paramEdit)
                    i=atualizaUsuario(i,CUArq,BASE_URL,fn)
            else:
                teste=i['email'].split('@itl.org.br')
                if len(teste)==1:
                    if not (i['lockoutEnabled']==True):
                        i['lockoutEnabled']=True
                        i['isPublisher']=False
                        print('USUARIO NÃO LOCALIZADO: '+i['email']+' '+i['cpf']+' '+i['fullName'])
                        CUArq=i['position']
                        i=atualizaUsuario(i,CUArq,BASE_URL,fn)
                else:
                    print('EMAIL ITL')

        reg = r'\([\s\S]*\)'
        cargo2 = re.sub(reg, '', i['position'])
        if cargo2 not in cargosLista:
            cargosLista.append(cargo2)

        if 'Unidade' in vPosition:
            vPos=vPosition.split('Unidade')[1].replace(' ','').replace(')','')
            if (len(vPos)<3 and len(vPos)>5):
                print(vPos)
            usuariosUnidade.append({'email':i['userName'],'localizacao':vPos})
            # if "B13" in vPosition:
            #     continue
        elif('DEX' in vPosition):
            if grupo:
                usuariosUnidade.append({'email':i['userName'],'localizacao':'DEX'})
            continue
        else:
            teste=i['email'].split('@itl.org.br')
            if (len(teste)>1):
                continue
            if (i['lockoutEnabled']==True):
                continue
            continue
 
    if filtroUsuarioEmail:
        usuariosUnidade.append({'email':filtroUsuarioEmail,'localizacao':''})

    total_arquivos = 0
    total_assinaturas = 0
    usuarioComMaisUsoDocumento = ''
    usuarioComMaisUsoAssinatura = ''
    valorMaisAltoDocumento=0
    qtdAssinaturaUsuarioDocumento = 0
    qtdAssinaturaUsuarioAssinatura = 0

    data2 = pd.DataFrame(pd.read_excel('TAE.xlsx'), columns=['AUTOR', 'ID.','DESTINATÁRIO','HASH','DATA DE CRIAÇÃO'])
    hashAnterior=0

    teste = []

    for i, value in enumerate(usuariosUnidade):
        enviosAutor = data2[data2["AUTOR"] == value['email']]
        tempDocs=0
        tempAss=0

        if enviosAutor.index.empty:
            continue

        for i,hashAtual in enumerate(enviosAutor["HASH"]):
            tempAss+=1
            total_assinaturas+=1
            if hashAtual!=hashAnterior:
                tempDocs+=1
                total_arquivos+=1

            hashAnterior=hashAtual

        if tempDocs>valorMaisAltoDocumento:
           valorMaisAltoDocumento=tempDocs
           usuarioComMaisUsoDocumento=value['email']
           qtdAssinaturaUsuarioDocumento=tempAss
        if tempAss>qtdAssinaturaUsuarioAssinatura:
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

            if indice+1==len(teste) and not valid:
                # print(str(indice) + ' ' + value['localizacao'])
                teste.append({
                    'unidade':value['localizacao'],
                    'envios':tempAss,
                    'usuarios':[value['email']]
                })
                # print(value['email'])
                break

        if len(teste)==0:
            teste.append({
                'unidade':value['localizacao'],
                'envios':tempAss,
                'usuarios':[value['email']]
            })



        # print(value['email'] + " " + str(tempDocs) + " " + str(tempAss) + " "+ value['localizacao'])
    def myFunc(e):
        return e['envios']
    teste.sort(key=myFunc)

    for xx in teste:
        if xx['unidade']=='B13':
            print(xx['envios'])
    
    print('-------')
    teste1 = json.dumps(teste)
    dff = pd.read_json(teste1)
    dff.to_csv('file.csv')
    print("Total de Arquivos: "+str(total_arquivos))
    print("Total de Assinaturas: "+str(total_assinaturas))
    print("Usuário com mais envio de documentos: "+usuarioComMaisUsoDocumento)
    print("Qtd de documentos do usuário: "+str(valorMaisAltoDocumento))
    print("Qtd de assinaturas do usuário: "+str(qtdAssinaturaUsuarioDocumento))
    print("Usuário com mais assinaturas: "+usuarioComMaisUsoAssinatura)
    print("Qtd de assinaturas do usuário: "+str(qtdAssinaturaUsuarioAssinatura))
    print("Qtd usuários selecionados: "+str(len(usuariosUnidade)))
    


atualizaCargo = False #Atualiza os cargos na plataforma TAE
recuperarTodos = True #Atualiza a lista de envios por UNIDADEs E DEX (TRUE) / UNIDADES (FALSE)
atualizaListaUsuarios = False #Atualiza arquivo local com usuários cadastrados
recuperaDocs = False #Recupera a lista de todos os documentos
recuperaDoc = False #Recupera um documento Especifico
filtroUsuarioEmail='' #Filtra informações de um usuário específico
outros(atualizaListaUsuarios,atualizaCargo,recuperarTodos,filtroUsuarioEmail,recuperaDocs,recuperaDoc) #Chama a função principal