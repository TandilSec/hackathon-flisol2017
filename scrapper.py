#!/usr/bin/env python2

# The MIT License (MIT)

# Copyright (c) 2017 TandilSec

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



# TODO:
# - Parse 'seguimientos' inner objects info following links.
# - Lot of hardcoded info that can be constants.

import requests
import json
import hashlib

try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup


URL_BASE = "http://www.autogestion.tandil.gov.ar/apex"
URL_DL = URL_BASE
URL_REQ_A = "%s/f?p=" % URL_BASE 
URL_REQ_B = "%s/wwv_flow.show" % URL_BASE
PLIEGOS = "pliegos"
SEGUIMIENTOS = "seguimientos"
URL_CONTEXT = {
    SEGUIMIENTOS: "102:27",
    PLIEGOS: "102:24"
}
HTML_CONTEXT = {
    SEGUIMIENTOS: "div",
    PLIEGOS: "li"
}
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:53.0) \
    Gecko/20100101 Firefox/53.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Host': 'www.autogestion.tandil.gov.ar',
}


class Scrapper(object):
    """Scrapper"""
    def __init__(self):
        super(Scrapper, self).__init__()
        self.context = None
        self.session = requests.Session()

    def setContextLimit(self, min_row, max_rows):
        """Sets the offset and limit for result rows"""
        self.min_row = min_row
        self.max_rows = max_rows

    def setContextPliegos(self, min_row, max_rows):
        """Sets context Pliegos with row config"""
        self.context = PLIEGOS
        self.setContextLimit(min_row, max_rows)

    def setContextSeguimientos(self, min_row, max_rows):
        """Sets context Seguimientos with row config"""
        self.context = SEGUIMIENTOS
        self.setContextLimit(min_row, max_rows)

    def contextSet(self):
        """Checks whether context is set or not"""
        if self.context is None:
            return False
        return True

    def prepare(self):
        """Prepares all the necessary information in order to
        fulfill all the requests accordingly"""

        # Make a first request to establish cookie within the session
        self.session.get("%s%s" % (URL_REQ_A, URL_CONTEXT[self.context]), headers=HEADERS)

        self.prepareData()

    def grabData(self):
        """Sets the content of the POST response with custom headers & data,
        in self.parsed_html for further use"""
        r = self.session.post(URL_REQ_B, self.data, headers=self.headers)
        self.parsed_html = BeautifulSoup(r.content, 'lxml')

    def getTitle(self, raw):
        """Returns current bidding title as string"""
        return raw.find('h3', attrs={'class': 't-SearchResults-title'}).text.strip()

    def getMiscs(self, raw):
        """Returns current bidding additional info as list"""
        return raw.findAll('span',
            attrs={'class': 't-SearchResults-misc'})

    def getDesc(self, raw):
        """Returns current bidding description as string"""
        return raw.find('p',
            attrs={'class': 't-SearchResults-desc'}).text.strip()

    def getDownload(self, link_title, link):
        r = self.session.get(link)
        data = BeautifulSoup(r.content, 'lxml')
        parsers = {
            "Items": self.getItems,
            "Cotizaciones": self.getCotizaciones,
            "Adjudicaciones": self.getAdjudicaciones,
            "Orden/es de Compra": self.getOrdenesDeCompra,
        }
        return parsers[link_title](data)

    def getItems(self, data):
        return {}

    def getInvitados(self, data):
        return {}

    def getCotizaciones(self, data):
        return {}

    def getAdjudicaciones(self, data):
        return {}

    def getOrdenesDeCompra(self, data):
        return {}

    def processData(self):
        """Iterates through HTML chunks finding the information needed for
        each context. Stores it as a dict in self.results"""
        licits_raw = self.parsed_html.findAll(HTML_CONTEXT[self.context],
                                              attrs={'class': 't-SearchResults-item'})

        self.results = {}
        for licit_raw in licits_raw:
            dls = {}

            title = self.getTitle(licit_raw)

            if self.context == SEGUIMIENTOS:
                results = {}
                miscs = self.getMiscs(licit_raw)
                apertura = miscs[0].text.split(':')[1].strip()
                try:
                    presupuesto = float(miscs[1].text.split(':')[1].strip().split("$")[1].strip())
                except:
                    presupuesto = 0

                results['apertura'] = apertura
                results['presupuesto'] = presupuesto

                for i in range(2, len(miscs)):
                    link = miscs[i].find('a')
                    link_title = link.text
                    linkstr = str(link)
                    link = linkstr[linkstr.index("f?p"):linkstr.index("',{")]
                    link = link.replace("\\u0026", "&")
                    link = "%s/%s" % (URL_DL, link)
                    results[link_title] = self.getDownload(link_title, link)

                self.results[title] = results

            elif self.context == PLIEGOS:
                results = {}
                desc = self.getDesc(licit_raw)

                for misc in self.getMiscs(licit_raw):
                    text = misc.text.strip()
                    if text == "" or "Descargar el" in text:
                        continue

                    if ":" in text:
                        key, value = text.split(":", 1)
                        results[key] = value.strip()
                    elif "Fecha de Apertura " in text:
                        results["fecha_apertura"] = text.split("Fecha de Apertura ")[1]

                for dl in licit_raw.findAll('a'):
                    dlstr = str(dl)
                    dls[dl.text.strip()] = "%s%s" % (URL_DL,
                        dlstr[dlstr.index("f?p"):dlstr.index("\">")])

                results['title'] = title
                results['descripcion'] = desc
                results['download'] = dls

                # Since each entry does not have an ID, we make one.
                sha1 = hashlib.sha1()
                sha1.update((title + desc).encode('utf-8'))
                shaid = sha1.hexdigest()
                self.results[shaid] = results

    def scrap(self):
        """Core of the scrapper. Basically does all the work.
        First request is used or will be used to get dynamically cookie info.
        Second request is the POST which asks for the data we're looking for.
        Finally, it stores all the results in dict fashion format.
        """
        if not self.contextSet():
            return False

        self.prepare()
        self.grabData()
        self.processData()

    def prepareData(self):
        """Configues POST data to be sent according to current context"""
        if self.context == SEGUIMIENTOS:
            step_id = "27"
            instance = "11313251178256"
            x01 = "36151191885338894"
        elif self.context == PLIEGOS:
            step_id = "24"
            instance = "6658277503553"
            x01 = "35314433335395863"

        self.data = "p_request=APXWGT" \
            "&p_flow_id=102" \
            "&p_flow_step_id=%s" \
            "&p_instance=%s" \
            "&p_debug=" \
            "&p_widget_action=paginate" \
            "&p_pg_min_row=%s" \
            "&p_pg_max_rows=%s" \
            "&p_pg_rows_fetched=0" \
            "&x01=%s" \
            "&p_widget_name=classic_report" % \
            (step_id, instance, self.min_row, self.max_rows, x01)

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:53.0) \
            Gecko/20100101 Firefox/53.0',
            'Accept': 'text/html, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'http://www.autogestion.tandil.gov.ar/apex/f?p=%s' %
                URL_CONTEXT[self.context],
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Length': str(len(self.data)),
            'Connection': 'keep-alive',
            'Host': 'www.autogestion.tandil.gov.ar'
        }

    def toFile(self, format="json"):
        """Prints results to file using parametrized format"""
        if format == "json":
            with open('data_%s.json' % self.context, 'w') as outfile:
                json.dump(self.results, outfile, sort_keys=True, indent=4)
            pass
        elif format == "csv":
            pass


if __name__ == '__main__':
    # Initializing the scrapper
    s = Scrapper()

    # Setting up Pliegos de Licitaciones with first 100 rows.
    print("[*] Scrapeando pliegos")
    s.setContextPliegos(1, 10)
    s.scrap()
    s.toFile()

    # Setting up Seguimientos de Licitaciones with first 100 rows.
    print("[*] Scrapeando seguimientos")
    s.setContextSeguimientos(1, 10)
    s.scrap()
    s.toFile()

