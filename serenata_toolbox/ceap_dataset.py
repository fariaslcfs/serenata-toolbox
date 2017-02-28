import os.path
from datetime import date as d

from urllib.request import urlretrieve
from zipfile import ZipFile
import numpy as np
import pandas as pd

from .reimbursements import Reimbursements
from .xml2csv import convert_xml_to_csv

class CEAPDataset:
    def __init__(self, path):
        self.path = path

    def fetch(self):
        urls = ['http://www.camara.gov.br/cotas/AnoAtual.zip',
                'http://www.camara.gov.br/cotas/AnoAnterior.zip',
                'http://www.camara.gov.br/cotas/AnosAnteriores.zip']
        filenames = map(lambda url: url.split('/')[-1], urls)

        for url, filename in zip(urls, filenames):
            zip_file_path = os.path.join(self.path, filename)
            urlretrieve(url, zip_file_path)
            zip_file = ZipFile(zip_file_path, 'r')
            zip_file.extractall(self.path)
            zip_file.close()
            os.remove(zip_file_path)

        urlretrieve('http://www2.camara.leg.br/transparencia/cota-para-exercicio-da-atividade-parlamentar/explicacoes-sobre-o-formato-dos-arquivos-xml',
                    os.path.join(self.path, 'datasets-format.html'))

    def convert_to_csv(self):
        for filename in ['AnoAtual', 'AnoAnterior', 'AnosAnteriores']:
            xml_path = os.path.join(self.path, '{}.xml'.format(filename))
            csv_path = xml_path.replace('.xml', '.csv')
            convert_xml_to_csv(xml_path, csv_path)

    def translate(self):
        for filename in ['AnoAtual', 'AnoAnterior', 'AnosAnteriores']:
            csv_path = os.path.join(self.path, '{}.csv'.format(filename))
            self.__translate_file(csv_path)

    def clean(self):
        reimbursements = Reimbursements(self.path)
        f_path = os.path.join(self.path, 'reimbursements.xz')
        if not os.path.exists(f_path):
            dataset = reimbursements.group(reimbursements.receipts)
            reimbursements.write_reimbursement_file(dataset)
        current_year = d.today().year + 1
        counter = 0
        for year in range(2009, current_year):
            f_path = os.path.join(self.path, 'reimbursements_{}.xz'.format(str(year)))
            if os.path.exists(f_path):  # not the best way but... another hack
                counter += 1
        if counter == 0:
            reimbursements.split_reimbursements()  # creates one reimbursement file per year

    def __translate_file(self, csv_path):
        output_file_path = csv_path \
            .replace('AnoAtual', 'current-year') \
            .replace('AnoAnterior', 'last-year') \
            .replace('AnosAnteriores', 'previous-years') \
            .replace('.csv', '.xz')

        data = pd.read_csv(csv_path,
                           dtype={'idedocumento': np.str,
                                  'idecadastro': np.str,
                                  'nucarteiraparlamentar': np.str,
                                  'codlegislatura': np.str,
                                  'txtcnpjcpf': np.str,
                                  'numressarcimento': np.str})
        data.rename(columns={
            'idedocumento': 'document_id',
            'txnomeparlamentar': 'congressperson_name',
            'idecadastro': 'congressperson_id',
            'nucarteiraparlamentar': 'congressperson_document',
            'nulegislatura': 'term',
            'sguf': 'state',
            'sgpartido': 'party',
            'codlegislatura': 'term_id',
            'numsubcota': 'subquota_number',
            'txtdescricao': 'subquota_description',
            'numespecificacaosubcota': 'subquota_group_id',
            'txtdescricaoespecificacao': 'subquota_group_description',
            'txtfornecedor': 'supplier',
            'txtcnpjcpf': 'cnpj_cpf',
            'txtnumero': 'document_number',
            'indtipodocumento': 'document_type',
            'datemissao': 'issue_date',
            'vlrdocumento': 'document_value',
            'vlrglosa': 'remark_value',
            'vlrliquido': 'net_value',
            'nummes': 'month',
            'numano': 'year',
            'numparcela': 'installment',
            'txtpassageiro': 'passenger',
            'txttrecho': 'leg_of_the_trip',
            'numlote': 'batch_number',
            'numressarcimento': 'reimbursement_number',
            'vlrrestituicao': 'reimbursement_value',
            'nudeputadoid': 'applicant_id',
        }, inplace=True)

        data['subquota_description'] = \
            data['subquota_description'].astype('category')

        categories = {
            'assinatura de publicações':
                'Publication subscriptions',
            'combustíveis e lubrificantes.':
                'Fuels and lubricants',
            'consultorias, pesquisas e trabalhos técnicos.':
                'Consultancy, research and technical work',
            'divulgação da atividade parlamentar.':
                'Publicity of parliamentary activity',
            'emissão bilhete aéreo':
                'Flight ticket issue',
            'fornecimento de alimentação do parlamentar':
                'Congressperson meal',
            'hospedagem ,exceto do parlamentar no distrito federal.':
                'Lodging, except for congressperson from Distrito Federal',
            'locação ou fretamento de aeronaves':
                'Aircraft renting or charter of aircraft',
            'locação ou fretamento de embarcações':
                'Watercraft renting or charter',
            'locação ou fretamento de veículos automotores':
                'Automotive vehicle renting or charter',
            'manutenção de escritório de apoio à atividade parlamentar':
                'Maintenance of office supporting parliamentary activity',
            'participação em curso, palestra ou evento similar':
                'Participation in course, talk or similar event',
            'passagens aéreas':
                'Flight tickets',
            'passagens terrestres, marítimas ou fluviais':
                'Terrestrial, maritime and fluvial tickets',
            'serviço de segurança prestado por empresa especializada.':
                'Security service provided by specialized company',
            'serviço de táxi, pedágio e estacionamento':
                'Taxi, toll and parking',
            'serviços postais':
                'Postal services',
            'telefonia':
                'Telecommunication',
            'aquisição de material de escritório.':
                'Purchase of office supplies',
            'aquisição ou loc. de software; serv. postais; ass.':
                'Software purchase or renting; Postal services; Subscriptions',
            'locação de veículos automotores ou fretamento de embarcações ':
                'Automotive vehicle renting or watercraft charter',
            'locomoção, alimentação e  hospedagem':
                'Locomotion, meal and lodging',
        }
        
        categories = [categories[cat] for cat in data['subquota_description'].cat.categories]
        data['subquota_description'].cat.rename_categories(categories, inplace=True)
        data.to_csv(output_file_path, compression='xz', index=False, encoding='utf-8')

        return output_file_path
