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
import base64
import os

warnings.filterwarnings('ignore')

tipo = config('TIPO')
login = config('LOGIN')
senha = config('SENHA')
_token = ''

cpfInvalido='./log/_CPF_INVALIDO.txt'
desabilitado='./log/_DESABILITADO.txt'
naoLocalizado='./log/_NAO_LOCALIZADO.txt'
contagemDeUso='./log/_CONSUMO.csv'
usuariosTae='./log/_usuariosTAE.json'
usuariosGestao='./log/usuariosSS.csv'
assinaturas='./log/TAE.xlsx'
liberadosPorChamado='./log/usuariosLiberados.json'
reusoEmails='./log/_REUSO_EMAILS.json'
# corrigirCPF='./log/CORRIGIR_CPF.txt'

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
    print("---- ATUALIZA_USUARIO")
    """Function printing python version."""
    i['position'] = CUArq
    GroupRoles=[]
    if i['isAdministrator']:
        GroupRoles.append(1)
        GroupRoles.append(2)
        GroupRoles.append(3)
        GroupRoles.append(4)
        GroupRoles.append(5)
    req = {}
    req = {
        'url': BASE_URL+'identityintegration/v2/administrators/user',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+_token
        },
        'verify':False,
        'json':{
            "id":i['id'],
            "fullName": i['fullName'],
            "phoneNumber":fn,
            "position": CUArq,
            "isPublisher":i['isPublisher'],
            "GroupRoles":GroupRoles,
            "isDisabled":i['lockoutEnabled']
        }
    }

    try:
        rreq = requests.put(**req,timeout=500)
        if(rreq.status_code==401):
            print("Renovando Token!")
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
    except Exception as e:
        print(e)
        exit()
    except:
        print("deu ERRO!")
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
        _token = rLogin['data']['token']
        # os.environ['TOKEN'] =rLogin['data']['token']
        return _token
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
        'url': BASE_URL+'documents/v2/publicacoes/'+idTAE,
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+_token
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
            "authorization": "Bearer "+_token
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
        with open(usuariosTae, 'w', encoding='utf-8') as f:
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
        'url': BASE_URL+'documents/v2/publicacoes/pesquisas?PaginaAtual=1&TamanhoPagina=0',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+_token
        },
        'json': {
            "pesquisarEmTodaEmpresa": True
        },
        'verify':False
    }
    reqDocs = requests.get(**req)
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
def reqDoc(paginaAtual,emailRemetente,tamanhoPagina):
    print(f'Buscando {(tamanhoPagina*paginaAtual)-tamanhoPagina} a {tamanhoPagina*paginaAtual}')
    req = {
        'url': f'{BASE_URL}documents/v2/publicacoes/pesquisas?PaginaAtual={paginaAtual}&TamanhoPagina={tamanhoPagina}',
        'headers': {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "Bearer "+_token
        },
        'json': {
            "email":emailRemetente,
            "pesquisarEmTodaEmpresa": True
        },
        'verify':False
    }
    

    return req

def listaIdsDocsPorUsuarioRemetente(emailRemetente):
    """Function printing python version."""
    req = {}
    paginaAtual = 1
    tamanhoPagina = 50
    qtdArquivos = 0
    idsArquivos=[]

    while True:
        paginaAtual
        req = reqDoc(paginaAtual,emailRemetente,tamanhoPagina)
        reqDocs = requests.post(**req)
        if reqDocs.status_code==401 or reqDocs.status_code==400:
            req['headers']['authorization'] = "Bearer "+gerarToken()
            reqDocs = requests.post(**req)

        if reqDocs.status_code == requests.codes['ok']:
            r = json.loads(reqDocs.text)
            dados=r['data']
            if (qtdArquivos==0):
                qtdArquivos=dados['total']
            
            for doc in dados['registro']:
                if(doc['status']==2 and doc['usuario']['email']==emailRemetente):
                    idsArquivos.append(doc['id'])
        else:
            print(reqDocs.raise_for_status)
            print('Erro!')
            exit()

        if (qtdArquivos>(tamanhoPagina*paginaAtual)):
            paginaAtual+=1
        else:
            break
    
    if not os.path.exists(f'./DOWNLOADS'):
        os.mkdir('./DOWNLOADS')
        os.mkdir(f'./DOWNLOADS/{emailRemetente}')
    
    if not os.path.exists(f'./DOWNLOADS/{emailRemetente}'):
        os.mkdir(f'./DOWNLOADS/{emailRemetente}')
    
    for id in idsArquivos:
        print(f'Baixando {id}...')
        req = {
            'url': f'{BASE_URL}documents/v1/publicacoes/{id}/download?tipoDownload=4',
            'headers': {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": "Bearer "+_token
            },
        }
        reqDocs = requests.get(**req)
        if reqDocs.status_code==401 or reqDocs.status_code==400:
            req['headers']['authorization'] = "Bearer "+gerarToken()
            reqDocs = requests.get(**req)

        if reqDocs.status_code == requests.codes['ok']:
            r = json.loads(reqDocs.text)
            b64 = base64.b64decode(r['data']['fileBytes'])
            with open(f'./DOWNLOADS/{emailRemetente}/{id}-{r['data']['fileName']}', 'wb') as f:
                f.write(b64)
# ------------------------------------------------------------------
def dadosUsuario(usuario,emailCheck,cpfCheck):
    """Function printing python version."""
    listaUsuarios=[]

    if cpfCheck=='67611150600':
        return []
    info='usuario,cpf,Nome,unidade,cargo,Email\n'
    atualizar=False
    Lines = open(usuariosGestao, 'r',encoding='utf-8-sig').readlines()
    for linex in Lines:
        if not (info in linex):
            atualizar=True
        break

    if atualizar:
        with open(usuariosGestao, 'r+',newline='',encoding='utf-8-sig') as file: 
            file_data = file.read().replace(';',',')
            file.seek(0)
            file.write(info + file_data)
            file.close()
            
    with open(usuariosGestao, newline='', encoding='utf-8-sig') as csvfile:
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
            if row['cpf'].replace('.','').replace('-','').rstrip()!=cpfCheck:
                # EDITAR >>
                emailReusado = json.load(open(reusoEmails))
                if emailCorreto in emailReusado:
                    print(">> EMAIL REUSADO - " +emailCorreto)
                    return []
                else:
                    print('>>CPF INVALIDO: '+row['cpf'].replace('.','').replace('-','')+">"+cpfCheck+" "+usuario)
                    # file1 = open(cpfInvalido, "a")  # append mode
                    # file1.write(row['cpf'].replace('.','').replace('-','')+">"+cpfCheck+" "+usuario+"\n")
                    # file1.close()
                    return []

            cargoOld=row['cargo'].replace(" (A)","").replace(" (a)","").strip().upper()
            unidadeOld = row['unidade'].replace(" ","")
            # un = unidadeOld.split('-')
            
            # if(un[len(un)-1]=='SENAT'):
                # del un[len(un)-1]
            
            # if len(un)==2:
                # nUn = un[1].replace("Nº","").replace("nº","").replace("n°","").replace("N°","")
            # elif len(un)==3:
                # nUn = (un[1]+un[2]).replace("Nº","").replace("nº","").replace("n°","").replace("N°","")
                # if len(nUn)<=5:
                    # nUn="Unidade"+nUn
            # elif len(un)==4:
                # nUn = (un[2]+un[3]).replace("Nº","").replace("nº","").replace("n°","").replace("N°","")
            # else:
                # nUn = "DEX"
            row['unidade'] = unidadeOld
            row['cargo'] = cargoOld
            row['CargoUnidade'] = cargoOld + " (" + row['unidade'] + ")"
            listaUsuarios.append(row)


    return listaUsuarios
# ------------------------------------------------------------------
def outros(atualizaListaUsuarios,atualizaCargo,grupo,filtroUsuarioEmail,recuperaDocs, recuperaDoc):
    """Function printing python version."""
    global _token
    
    if not (_token): _token=gerarToken() #Gera token de autenticação TAE
    
    if recuperaDocs:
        # recuperarDocLista()
        listaIdsDocsPorUsuarioRemetente(filtroUsuarioEmail)

    exit()
    
    if recuperaDoc:
        recuperarDocUnico(id)
    
    rReq2=[]
    if (atualizaListaUsuarios):
        rReq2=recuperarListaUsuarios()
    
    if not(rReq2):
        print("Carregando Arquivo")
        try:
            print("Local")
            f = open(usuariosTae)
            arqAssin = json.load(f)
            f.close()
        except:
            print("Online")
            arqAssin = recuperarListaUsuarios()
    else:
        print("Abrindo usuários Online")
        arqAssin = rReq2

    usuariosUnidade = [{'email':'tae@sestsenat.org.br','localizacao':'*ADMIN'}]
    cargosLista = []
    file1 = open(cpfInvalido, "a")  # append mode
    file1.write("\n\n"+(date.today()).strftime("%d/%m/%Y")+"\n")
    file1.close()
    file1 = open(naoLocalizado, "a")  # append mode
    file1.write("\n\n"+(date.today()).strftime("%d/%m/%Y")+"\n")
    file1.close()
    file1 = open(desabilitado, "a")  # append mode
    file1.write("\n\n"+(date.today()).strftime("%d/%m/%Y")+"\n")
    file1.close()
    for i in arqAssin['data']['registro']:
        vPosition = i['position']

        if filtroUsuarioEmail:
            if i['userName']==filtroUsuarioEmail:
                print("----- FILTRO_USUARIO_EMAIL")
            else:
                continue

        if len(i['cpf'])!=11:
            print("----- CADASTRO_CNPJ")
            if i['userName']=='pontoeletronico@sestsenat.org.br':
                atualizaCargo=False
                # usuariosUnidade.append({'email':i['userName'],'localizacao':'PONTO'})
            else:
                # print("CPF INVALIDO "+i['cpf']+">>>"+i['userName'])
                if not (i['lockoutEnabled']):
                    # print("DESABILITANDO>>>>")
                    print(i['userName'])
                    i['lockoutEnabled']=True
                    atualizaUsuario(i,i['position'],BASE_URL,fn)
                    file1 = open(cpfInvalido, "a")  # append mode
                    file1.write(i['userName']+"\n")
                    file1.close()
                    atualizaCargo=False
                    
                
                # if (i['userName']=='evandrooliveira@sestsenat.org.br' or 
                #     i['userName']=='liviaspadoni@sestsenat.org.br' or
                #     i['userName']=='lauragrandizoli@sestsenat.org.br' or
                #     i['userName']=='cezarjunior@sestsenat.org.br'):
                #     print("DESABILITANDO>>>>")
                #     if not (i['lockoutEnabled']):
                #         i['lockoutEnabled']=True
                #         atualizaUsuario(i,i['position'],BASE_URL,fn)
                    
                # print("CPF INVALIDO "+i['cpf']+">>>"+i['userName'])
                file1 = open(cpfInvalido, "a")  # append mode
                file1.write(i['userName']+"\n")
                file1.close()
                print(i['userName'])
                atualizaCargo=False

        if i['userName']=='ponto.a001@sestsenat.org.br':
            atualizaCargo=False

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
            
            novoAlias = userName.split('.tae')
            if (len(novoAlias)>1):
                userName = userName.replace(".tae","")
                validEmail = validEmail.replace(".tae","")
                
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
                CUArq=du[0]['CargoUnidade'].replace("(A)","").replace("(a)","").replace(" (A)","").replace(" (a)","")
                CArq=du[0]['cargo'].replace(" II","").replace(" I","").replace(" (A)","").replace(" (a)","")

                siglaUnidade=''
                edit=False
                paramEdit=''
                # i['isPublisher']=True

                if UArq!='DEX':
                    siglaUnidade=UArq.replace("Unidade","")[0]
                    # print(CArq)
                    # print(siglaUnidade)

                usuariosLiberados = json.load(open(liberadosPorChamado))

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
                    or CArq=='GERENTE DE UNIDADE'
                    or CArq=='SUPERVISOR'):
                    if not i['isPublisher']:
                        i['isPublisher']=True
                        edit=True
                        paramEdit=paramEdit+'/PUBLICADOR-DIRETOR/'
                    
                elif "TECNICO" in CArq:
                    if (siglaUnidade=="D" or siglaUnidade=="DN") and not i['isPublisher']:
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
                    print("DESABILITADO: ")
                    file1 = open(desabilitado, "a")  # append mode
                    file1.write(i['userName']+"\n")
                    file1.close()
                    i['lockoutEnabled']=False
                    edit=True
                    paramEdit=paramEdit+'/DESATIVADO-TRUE/'
                
                # if i['lockoutEnabled'] and not edit:
                #     print("DESABILITADO: ")
                #     file1 = open(desabilitado, "a")  # append mode
                #     file1.write(i['userName']+"\n")
                #     file1.close()
                #     continue
                    

                if(vPosition!=CUArq or edit):
                    # if not (edit):
                    #     print(vPosition)
                    #     print(CUArq)
                    #     print("/NOME-CARGO/"+paramEdit)
                    # if edit:
                    #     print(paramEdit)
                    i=atualizaUsuario(i,CUArq,BASE_URL,fn)
            else:
                emailITL=i['email'].split('@itl.org.br')
                # reativar = json.load(open("./log/REATIVAR.json"))

                # if len(emailITL)==1 and i['email']!='pontoeletronico@sestsenat.org.br':
                    # if (i['email'] in reativar and i['lockoutEnabled']==True):
                    #     print("Ativando: "+i['email'])
                    #     i['lockoutEnabled']=False
                    #     i=atualizaUsuario(i,CUArq,BASE_URL,fn)
                    # if not (i['lockoutEnabled']==True):
                    #     i['lockoutEnabled']=True
                    #     i['isPublisher']=False
                    #     print('USUARIO NÃO LOCALIZADO: '+i['email']+' '+i['cpf']+' '+i['fullName'])
                    #     CUArq=i['position']
                    #     file1 = open(naoLocalizado, "a")  # append mode
                    #     file1.write(i['userName']+"\n")
                    #     file1.close()
                    #     i=atualizaUsuario(i,CUArq,BASE_URL,fn)
                # else:
                    # print("----- ITL")
                    # print(i['email'])

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
                usuariosUnidade.append({'email':i['userName'],'localizacao':'*DEX'})
        elif('SUPERVISOR' in vPosition):
            usuariosUnidade.append({'email':i['userName'],'localizacao':'*SUPERVISOR'})
        elif('AUTOMATICO' in vPosition):
            usuariosUnidade.append({'email':i['userName'],'localizacao':'*PONTO'})
        else:
            emailITL=i['email'].split('@itl.org.br')
            if (len(emailITL)>1):
                usuariosUnidade.append({'email':i['userName'],'localizacao':'*ITL'})
            else:
                usuariosUnidade.append({'email':i['userName'],'localizacao':'*SEM_UNIDADE'})
 
    if filtroUsuarioEmail:
        usuariosUnidade.append({'email':filtroUsuarioEmail,'localizacao':''})

    total_arquivos = 0
    total_assinaturas = 0
    usuarioComMaisUsoDocumento = ''
    # usuarioComMaisUsoAssinatura = ''
    valorMaisAltoDocumento=0
    # qtdAssinaturaUsuarioDocumento = 0
    # qtdAssinaturaUsuarioAssinatura = 0

    try:
        data2 = pd.DataFrame(pd.read_excel(assinaturas), columns=['ID.','STATUS','HASH TOTVS','AUTOR','DATA DE CRIAÇÃO'])
    except Exception as e:
        print(e)
        print('Arquivo TAE não encontrado')
        exit()

    # print()

    # testeu=[]
    # testeu2=data2["AUTOR"].tolist()
    # for u in usuariosUnidade:
    #     testeu.append(u['email'])
    
    # set1 = set(testeu)
    # set2 = set(testeu2)

    # # Encontrando elementos em array1 que não estão em array2
    # elementos_exclusivos_em_array1 = set1 - set2 
    # print(elementos_exclusivos_em_array1)  # Output: {1, 2, 4}

    # # Encontrando elementos em array2 que não estão em array1
    # elementos_exclusivos_em_array2 = set2 - set1
    # print(elementos_exclusivos_em_array2)  # Output: {6, 7}
    # exit()

    consumoUnidade = []

    for i, value in enumerate(usuariosUnidade):
        enviosAutor = data2[data2["AUTOR"] == value['email']]
        # tempDocs=0
        # tempAss=0

        if enviosAutor.index.empty and value['localizacao']!='*SUPERVISOR':
            continue

        total_arquivos = enviosAutor.shape[0]
        total_assinaturas+=total_arquivos
        if (total_arquivos>valorMaisAltoDocumento and value['email']!='pontoeletronico@sestsenat.org.br'):
            usuarioComMaisUsoDocumento=value['email']
            valorMaisAltoDocumento=total_arquivos

        # for i,hashAtual in enumerate(enviosAutor["HASH"]):
        #     tempAss+=1
        #     total_assinaturas+=1
        #     if hashAtual!=hashAnterior:
        #         tempDocs+=1
        #         total_arquivos+=1

        #     hashAnterior=hashAtual

        # if tempDocs>valorMaisAltoDocumento:
        #    valorMaisAltoDocumento=tempDocs
        #    usuarioComMaisUsoDocumento=value['email']
        #    qtdAssinaturaUsuarioDocumento=tempAss
        # if tempAss>qtdAssinaturaUsuarioAssinatura:
        #    usuarioComMaisUsoAssinatura=value['email']
        #    qtdAssinaturaUsuarioAssinatura=tempAss



        for indice,valor in enumerate(consumoUnidade):
            valid=False
            if(valor['unidade']==value['localizacao']):
                valor['usuarios'].append(value['email'])
                valor['envios']=(valor['envios']+total_arquivos)
                valid=True
                break

            if indice+1==len(consumoUnidade) and not valid:
                consumoUnidade.append({
                    'unidade':value['localizacao'],
                    'envios':total_arquivos,
                    'usuarios':[value['email']]
                })
                break

        if len(consumoUnidade)==0:
            consumoUnidade.append({
                'unidade':value['localizacao'],
                'envios':total_arquivos,
                'usuarios':[value['email']]
            })



        # print(value['email'] + " " + str(tempDocs) + " " + str(tempAss) + " "+ value['localizacao'])
    def myFunc(e):
        return e['envios']
    consumoUnidade.sort(key=myFunc)

    # for xx in consumoUnidade:
        # if xx['unidade']=='B13':
            # print(xx['envios'])
    
    print('-------')
    teste1 = json.dumps(consumoUnidade)
    dff = pd.read_json(teste1)
    dff.to_csv(contagemDeUso)
    # print("Total de Arquivos: "+str(total_arquivos))
    print("Total de Arquivos: "+str(total_assinaturas))
    print("Usuário com mais envio de documentos: "+usuarioComMaisUsoDocumento)
    print("Qtd de documentos do usuário: "+str(valorMaisAltoDocumento))
    # print("Qtd de assinaturas do usuário: "+str(qtdAssinaturaUsuarioDocumento))
    # print("Usuário com mais assinaturas: "+usuarioComMaisUsoAssinatura)
    # print("Qtd de assinaturas do usuário: "+str(qtdAssinaturaUsuarioAssinatura))
    print("Qtd usuários selecionados: "+str(len(usuariosUnidade)))
    
atualizaCargo = False #Atualiza os cargos na plataforma TAE
recuperarTodos = True #Atualiza a lista de envios por UNIDADEs E DEX (TRUE) / UNIDADES (FALSE)
atualizaListaUsuarios = False #Atualiza arquivo local com usuários cadastrados
recuperaDocs = True #Recupera a lista de todos os documentos
recuperaDoc = False #Recupera um documento Especifico
filtroUsuarioEmail='deividaraujo@sestsenat.org.br'
outros(atualizaListaUsuarios,atualizaCargo,recuperarTodos,filtroUsuarioEmail,recuperaDocs,recuperaDoc) #Chama a função principal

# import xmltodict
# import jsonf


# def t():
#     # Abrir o arquivo XML e ler seu conteúdo
#     with open('testexml.xml', 'r') as arquivo_xml:
#         # Converter XML para um dicionário Python
#         dados_dict = xmltodict.parse(arquivo_xml.read())
#     print(dados_dict["definition"]["mapping"]["metadatas"][0])
#     # Converter o dicionário Python para JSON
#     dados_json = json.dumps(dados_dict)
#     # print()

#     # Salvar os dados JSON em um arquivo
#     with open('dados.json', 'w') as arquivo_json:
#         arquivo_json.write(dados_json)

# t()