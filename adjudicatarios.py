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

import json


if __name__ == '__main__':
    # Abrir el archivo
    with open("output/data_seguimientos.json", "r") as f:
        seguimientos = json.load(f)

    adjudicatarios = {}

    for nombre, licitacion in seguimientos.items():
        if len(licitacion["Adjudicaciones"]) > 0:
            for adjudicacion in licitacion["Adjudicaciones"]:
                razon_social = adjudicacion["Razon Social"]

                if razon_social not in adjudicatarios:
                    adjudicatarios[razon_social] = {"razon_social": razon_social,
                                                    "cantidad": 0,
                                                    "costo_total": 0}

                adjudicatarios[razon_social]["cantidad"] += float(adjudicacion["Cant. Adj."])
                adjudicatarios[razon_social]["costo_total"] += float(adjudicacion["Costo T."])

    adjudicatarios = [v for x,v in adjudicatarios.items()]

    with open("output/adjudicatarios.json", "w") as f:
        json.dump(adjudicatarios, f, sort_keys=True, indent=4)
