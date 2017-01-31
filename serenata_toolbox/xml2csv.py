import json
import os
import sys
from csv import DictWriter
from datetime import datetime
from errno import ENOENT
from io import StringIO

from bs4 import BeautifulSoup


class Xml2Csv:

    def __init__(self, xml_path, csv_path):

        # check if XML exists
        if not os.path.exists(xml_path):
            raise FileNotFoundError(ENOENT, os.strerror(ENOENT), xml_path)

        # check if CSV directory exists
        if not os.path.exists(os.path.dirname(csv_path)):
            csv_dir = os.path.dirname(csv_path)
            raise FileNotFoundError(ENOENT, os.strerror(ENOENT), csv_dir)

        self.count = 0
        self.xml_path = xml_path
        self.csv_path = csv_path
        self.data_dir = os.path.dirname(xml_path)
        self.csv_header = tuple(self.get_csv_header())

    def convert(self):
        """Converts the XML file to a file in CSV format"""
        if os.stat(self.xml_path).st_size < 2 ** 10:
            self.output(self.xml_path, ' is empty.')
            return

        self.output('Creating the CSV file')
        self.create_csv()

        self.output('Reading the XML file')
        for data in self.parser():
            self.write_csv_row(data)

        print('')  # clean the last output (the one with end='\r')
        self.output('Done!')

    def parser(self, **kwargs):
        """
        Parses the XML yielding a string in JSON format for each record found.
        """
        encoding = kwargs.get('encoding', 'utf-16')
        with open(self.xml_path, encoding=encoding) as handler:
            soup = BeautifulSoup(handler, 'xml')
            for tag in soup.orgao.DESPESAS.children:
                fields = {field.name: field.text for field in tag.contents}
                yield json.dumps(fields)

    def get_csv_header(self, **kwargs):
        """
        Generator that yields the CSV headers reading them from a HTML file
        (e.g. datasets-format.html).
        """
        kwargs['filename'] = kwargs.get('filename', 'datasets-format.html')
        html_path = os.path.join(self.data_dir, kwargs['filename'])

        yield 'ideDocumento'  # this field is missing from the reference
        with open(html_path, 'rb') as fh:
            parsed = BeautifulSoup(fh.read(), 'lxml')
            for row in parsed.select('.tabela-2 tr'):
                try:
                    yield row.select('td')[0].text.strip()
                except IndexError:
                    pass

    def create_csv(self):
        """Creates the CSV file with the headers (must be a list)"""
        with open(self.csv_path, 'w') as fh:
            writer = DictWriter(fh, fieldnames=self.csv_header)
            writer.writeheader()

    def write_csv_row(self, json_content):
        """
        Gets a string in the JSON format and saves it to the CSV.
        """
        with StringIO() as ioh:
            writer = DictWriter(ioh, fieldnames=self.csv_header)
            writer.writerow(json.loads(json_content))
            content = ioh.getvalue()

        self.count += 1
        self.output_count()

        with open(self.csv_path, 'a') as fh:
            print(content, file=fh)

    def output_count(self):
        msg = 'Writing record #{:,} to the CSV'
        self.output(msg.format(self.count), end='\r')

    @staticmethod
    def output(*args, **kwargs):
        """Helper to print messages with a date/time marker"""
        now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        return print(now, *args, **kwargs)


def convert_xml_to_csv(xml_path, csv_path):
    xml2csv = Xml2Csv(xml_path, csv_path)
    xml2csv.convert()


if __name__ == "__main__":
    XML_PATH = sys.argv[1]
    CSV_PATH = sys.argv[2]
    convert_xml_to_csv(XML_PATH, CSV_PATH)
