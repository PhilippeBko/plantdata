import sys
import copy

from datetime import datetime
import re

from PyQt5 import QtCore, QtSql, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QAbstractItemView, QFileDialog, QHeaderView, QTableView, QTextEdit, QSpinBox, QComboBox, QDoubleSpinBox, QLineEdit, QStyleOptionViewItem, QDialogButtonBox, QStyledItemDelegate, QDialog, QMainWindow, QApplication, QLabel, QFrame, QWidget, QSizePolicy, QHBoxLayout, QPushButton, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QDateTime, QSortFilterProxyModel, QItemSelectionModel, QEvent
#from PyQt5.QtTest import QTest
from commons import get_reference_field, list_db_fields, get_str_value, flower_reg_pattern, fruit_reg_pattern
from class_synonyms import PNSynonym
from occ_model import PN_taxa_resolution_model
import pandas as pd
import math as mt
#from occ_model import PN_occ_model
#from import_csv import *

#structure of the trees tables
#synonyms for database value
dict_strata = {
    "understorey": [1, "sous-bois", "sotobosque", "understory"], "sub-canopy": [2, "sous-canopée", "sub-cubierta"], 
    "canopy": [3, "canopée", "cubierta"], "emergent": [3, "émergent","emergente"]
}

dict_month = {
    1: ["enero","january","janvier", "janv.", "jan.", "ene."], 2: ["febrero","february", "février", "feb.", "fev.", "fév."], 3: ["marzo", "march", "mars"],
    4: ["abril", "april", "avril"], 5: ["mayo", "may", "mai"], 6: ["junio", "june", "juin"],
    7: ["julio", "july", "juillet"], 8: ["agosto", "august", "août", "aug.", "ago."], 9: ["septiembre", "september", "septembre", "sept.", "sep"],
    10: ["octubre", "october", "octobre", "oct."], 11: ["noviembre", "november", "novembre", "nov."], 12: ["diciembre", "december", "décembre", "déc.", "dec.", "dic."]
}

list_typeplot = ["Circle", "Point", "Rectangle"]
list_month = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
list_strata = ["", "Understorey", "Sub-canopy", "Canopy", "Emergent"]

#structure of both tables plots and trees
dict_db_plot = {
                "id_plot": {"value" : None, "type" : 'integer', 'enabled': False}, 
                "collection": {"value" : None, "type" : 'text', "editable" : True}, 
                "locality": {"value" : None, "type" : 'text', "editable" : True}, 
                "plot": {"value" : None, "type" : 'text'}, 
                "longitude": {"value" : None, "type" : 'numeric', "min": -180, "max": 180, "decimal": 8}, 
                "latitude": {"value" : None, "type" : 'numeric', "min": -90, "max": 90, "decimal": 8}, 
                "altitude": {"value" : None, "type" : 'numeric'},                 
                "type": {"value" : None, "type" : 'text', "items" : list_typeplot},                
                "width": {"value" : None, "type" : 'numeric'},
                "radius": {"value" : None, "type" : 'numeric', "visible": False},
                "length": {"value" : None, "type" : 'numeric'},
                "area" : {"value": None, "enabled": False, "visible": True}
                }
dict_db_tree = {
                "id_tree": {"value" : None, "type" : 'integer', 'enabled': False},                
                "identifier":  {"value" : None, "type" : 'text',"synonyms" : ['identifiant', 'code', 'number', 'tree', 'id']},                
                "taxaname" : {"value" : None, "type" : 'text'}, 
                "month": {"value" : None, "type" : 'integer', "items" : list_month, "default":datetime.now().month}, 
                "year": {"value" : None, "type" : 'integer', "min": 1900, "max": datetime.now().year, "default": datetime.now().year}, 
                "strata": {"value" : None, "type" : 'text', "items": list_strata},
                "stems": {"value" : None, "type" : 'integer', "min": 1, "default":1, "tip": 'Number of stems at Breast Height [1m30]',"synonyms" : ['nb_stem', 'nb_tiges', 'tiges', 'tronc']}, 
                "dbh": {"value" : None, "type" : 'numeric', "unit" : 'cm', "min": 0, "max": 500, "tip": 'Diameter at Breast Height [1m30]-'}, 
                "height": {"value" : None, "type" : 'numeric', "unit" : 'm', "min": 0, "max": 50, "tip": 'Height of the tree'},
                "bark_thickness": {"value" : None, "type" : 'numeric', "unit" : 'mm', "min": 1, "tip": 'Thickness of tree bark'}, 
                "wood_density": {"value" : None, "type" : 'numeric', "unit" : 'g/cm3', "min": 0.1, "max": 2, "decimal": 5, "tip": 'Density of a wood core'}, 
                "leaf_sla": {"value" : None, "type" : 'numeric', "unit" : 'mm²/mg', "min": 1, "max": 50, "decimal": 5, "tip": 'Specific Leaf Area'}, 
                "leaf_area": {"value" : None, "type" : 'numeric', "unit" : 'mm²', "min": 1, "tip": 'Area of a leaf unit'}, 
                "leaf_ldmc": {"value" : None, "type" : 'numeric', "unit" : 'mg/g', "min": 10, "max": 1000, "tip": 'Leaf Dry Matter Content'},
                "x": {"value" : None, "type" : 'numeric', "min": 0}, 
                "y": {"value" : None, "type" : 'numeric', "min": 0}, 
                "notes":  {"value" : None, "type" : 'memo',"synonyms" : ['comment', 'comments', 'commentaire', 'note']}, 
                "flower": {"value" : None, "type" : 'boolean',"synonyms" : ['fleur', 'phenology']}, 
                "fruit": {"value" : None, "type" : 'boolean',"synonyms" : ['fruit', 'phenology']}, 
                "dead": {"value" : None, "type" : 'boolean', "default": False},
                "time_updated": {"value" : None, "type" : 'date', 'enabled': False},
                "history": {"value" : None, "type" : 'integer', 'enabled': False, 'visible': False}
                }
dbh_perimeter_synonyms = ["perimeter", "perim.", "périmètre", "périm.", "perimetro", "circumference", 
                      "circonférence", "circonf", "circ.", "girth", "circunferencia", "circ"]

dict_db_ncpippn = dict_db_plot | dict_db_tree
#default parameters
PLOT_DEFAULT_DECIMAL = 2
DBASE_DATETIME_FORMAT = "yyyy-MM-dd hh:mm:ss.zzz t"
DBASE_SCHEMA = 'plots'
DBASE_SCHEMA_TAXONOMY = 'taxonomy'
DBASE_SCHEMA_TREES = DBASE_SCHEMA + '.trees'
DBASE_SCHEMA_PLOTS = DBASE_SCHEMA + '.plots'

#TODO : Uniformize db_definition between plots, commons and pn_occurrences

#add synonyms definition from commons (if field exists !)
for field_name, field_def in dict_db_ncpippn.items():
    field_db = get_reference_field(field_name)
    if field_db:
        synonyms = list_db_fields[field_db]["synonyms"]
        field_def["synonyms"] = synonyms
dict_db_ncpippn["dbh"]["synonyms"] += dbh_perimeter_synonyms

def get_typed_value(field_name, field_value, for_sql = False):
#high level function, return the value casted to the right type, raised an error if not possible
    if field_name not in dict_db_ncpippn:
        return
    field_def = dict_db_ncpippn[field_name]
    _type = field_def["type"]
    if field_value is not None:
        try:
            if _type == 'integer':
                field_value = int(float(field_value))
            elif _type == 'numeric':
                _decimal = field_def.get("decimal", PLOT_DEFAULT_DECIMAL)
                field_value = round(float(field_value), _decimal)
            elif _type in ['text', 'memo']:
                field_value = str(field_value)
            elif _type == 'boolean':
                field_value = bool(field_value)
            elif _type == 'date':
                if isinstance(field_value, QDateTime):
                    field_value = field_value.toString(DBASE_DATETIME_FORMAT)
        except Exception :
            error_code = 1000
            msg = "Error in type casting for the field " + field_name
            raise ValueError(msg, error_code)
            field_value = None
    #transform to SQL value if flag for_sql True
    if for_sql:
        if not field_value:
            field_value = 'NULL'
        elif _type in ['text', 'memo', 'date']:
            field_value = field_value.replace("'", "''")
            field_value = "'" + field_value + "'"
    return field_value

def database_execute_query(sql_query):
#High level, execute query and return True or Value if included in query
    query = QtSql.QSqlQuery(sql_query)
    values_list = []
    if query.isActive():
        #success in query execution
        try:
            while query.next():
                value = query.value(0)
                values_list.append(value)
            if not values_list: #no returning value
                return True
            elif len(values_list) == 1: #One returning value
                return values_list[0]
            else:
                return values_list #list of returning value
        except:
            return True
    else:
        #error in query execution
        QMessageBox.warning(None, "Database Error", query.lastError().text())
        return False
        

# def createConnection(db):
# #connect to db    
#     db.setHostName("localhost")
#     db.setDatabaseName("test")
#     db.setUserName("postgres")
#     db.setPassword("postgres")
#     #app2 = QApplication([])
#     if not db.open():
#         QMessageBox.critical(None, "Cannot open database", "Unable to open database, check for connection parameters", QMessageBox.Cancel)
#         return False
#     return True


class HighlightColumnDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        #if index.column() == self.column_value:
        painter.save()
        brush = QtGui.QBrush(QtGui.QColor(128, 128, 128, 50))  # Couleur rouge semi-transparente
        painter.fillRect(option.rect, brush)
        painter.restore()
        if not index.siblingAtColumn(1).data():
            font = QtGui.QFont()
            font.setItalic(True)
            index.model().itemFromIndex(index).setFont(font)

class CSVImporter(QDialog):
#The main class of the dialog
    def __init__(self, table_def):
        super().__init__()
        #final list of trees to be imported
        #dictionnary (identifier:id_plot) of trees imported already present in the table trees 
        self.dict_identifier_toUpdate = {}
        self.rows_imported = 0
        # load the GUI
        self.column_value = 2
        # if not table_def:
        #     table_def = copy.deepcopy(dict_db_ncpippn)
        self.dict_trees_import = table_def
        self.type_columns = None
        self.dataframe = None
        self.buttonOK = False
        self.window = uic.loadUi('pn_ncpippn_import.ui')
        validator = QtGui.QIntValidator(2, 2147483647)
        self.window.lineEdit.setValidator(validator)
        self.window.progressBar.setVisible(False)
       # self.headers = None
        self.window.pushButton_import.clicked.connect(self.load)
        self.window.button_previous.clicked.connect(lambda: self.navigate(False))
        self.window.button_next.clicked.connect(lambda: self.navigate(True))
        self.window.lineEdit.textChanged.connect(self.loadValue)
        self.window.button_search_errors.clicked.connect(self.search_nexttError)
        self.window.buttonbox_import.button(QDialogButtonBox.Ok).clicked.connect(self.validate)
        self.window.buttonbox_import.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        delegate = HighlightColumnDelegate()
        self.window.tblview_columns.setItemDelegateForColumn(self.column_value+1, delegate)

    def load(self, filename = None):
        def is_synonym(fieldref, fieldname):
        #return True if fieldname is equal or a synonym to fieldref
            fieldname = fieldname.strip(' ').lower()
            fieldref = fieldref.strip(' ').lower()
            if fieldref == fieldname:
                return True
            synonym = dict_db_ncpippn[fieldref].get("synonyms", None)
            if synonym and fieldname in synonym:
                return True
            return False

        #main function to load a csv file, or to open fileBowser
        import os
        if not isinstance(filename, str):
            filename = None
        try:
            os.path.exists(filename)
        except:
            filename = None

        if filename is None:
        #set parameters to QfileDialog
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            file_dialog = QFileDialog()
            file_dialog.setNameFilter("Fichiers CSV (*.csv)")
            file_dialog.setDefaultSuffix("csv")
            filename, file_type = file_dialog.getOpenFileName(None, "Import a CSV File", "", "CSV Files (*.csv);;All files (*)", options=options)
            if not filename: 
                return 
        import csv
        with open(filename, 'r', encoding='utf-8') as file:
            # Lire une portion du fichier pour l'analyse
            sample = file.readline()
            # Utiliser csv.Sniffer pour déduire le délimiteur
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        #read the csv file and set the rows and columns
        try:
            self.dataframe = pd.read_csv(filename, sep=delimiter, encoding='utf-8', low_memory=False, quotechar='"', skipinitialspace=True)
        except Exception as e:
            QMessageBox.critical(None, "Invalid Datasource", str(e), QMessageBox.Cancel)
            return
        #Test for lines
        if self.dataframe.shape[0] <= 0:
            QMessageBox.critical(None, "Invalid Datasource", "The file is empty", QMessageBox.Cancel)
            return
        
        self.dataframe.columns = self.dataframe.columns.str.lower()
        _summary = str(self.dataframe.shape[0]) + ' rows, ' + str(self.dataframe.shape[1]) + ' columns - current row:'
        self.window.label_summary.setText(_summary)
        self.window.linedit_source_file.setText (filename)
        #check for primary types excluding null-values
        self.type_columns = self.dataframe.dropna().dtypes
        key_header = None
        #checks for fieldref, types and values of input fields
        for header, _type in self.type_columns.items():
#TODO: eventually to get details for each colums in csv file
            # no_nullvalue = self.dataframe [header].dropna()
            # _type = _type.name
            # #object come from mixed or text columns (check for boolean first)
            # if _type == 'object':
            #     if all(str(val).lower() in ['true', 'false', 'oui', 'non'] for val in no_nullvalue):
            #         _type = 'boolean'
            #     else:
            #         _type = "text"
            #     self.type_columns[header] = _type
            # #float64 come from numeric and even integer if some null values
            # if _type == 'float64':
            #     try:
            #         if no_nullvalue.apply(lambda x: float(x).is_integer()).all():
            #             _type = 'integer'
            #     except:
            #         if pd.api.types.is_string_dtype(no_nullvalue):
            #             _type = "numeric"
            #     self.type_columns[header] = _type
            # #transpose types names to standard ones
            # try:
            #     _type = get_column_type("type")
            # except:
            #     pass
            # #Calculate duplicated value
            # duplicated_value = False
            # duplicated_value = no_nullvalue.duplicated().any()
            # count_non_null = self.dataframe [header].count()
            # minimum_value = no_nullvalue.min()
            # maximum_value = no_nullvalue.max()
            # key_header = {"column": header, "value": None, "type": _type,  "non null": count_non_null, 
            #               "duplicated": duplicated_value, "min" : minimum_value, "max" : maximum_value}
#END TODO
            #check for match betwwen key and header (check for synonyms), add dict import to column defition if found 
            for key, field_def in self.dict_trees_import.items():
                if is_synonym(key, header):
                    key_header = {"column": header, "value": None}
                    field_def["import"] = key_header
        
        #return if no column imported
        if not key_header:
            return
        
        #to create a dictionnary of identifier in the CSV file that already exists in the table trees (UPDATE)
        if self.dict_trees_import.get("identifier", None):
            if self.dict_trees_import["identifier"].get("import", None):
                column = self.dict_trees_import["identifier"]["import"]["column"]
                #get a list of unique non null identifier
                non_null_identifier = self.dataframe[column].dropna().unique().tolist()
                #create the dictionnary of updated identifier
                if non_null_identifier:
                    #clause_in = ", ".join(tab_identifier)
                    clause_in = ", ".join(["'{}'".format(item) for item in non_null_identifier])
                    sql_query = f"SELECT identifier, {DBASE_SCHEMA_TREES}.id_plot, plot FROM {DBASE_SCHEMA_TREES} JOIN {DBASE_SCHEMA_PLOTS} ON {DBASE_SCHEMA_TREES}.id_plot = {DBASE_SCHEMA_PLOTS}.id_plot WHERE identifier IN ({clause_in})" 
                    query = QtSql.QSqlQuery(sql_query)
                    self.dict_identifier_toUpdate = {}
                    while query.next():
                        self.dict_identifier_toUpdate[query.value("identifier")] = [query.value("id_plot"), query.value("plot")]
        self.loadValue ()
    
    def loadValue(self, index = 0):
    #load the line corresponding to index (connect with lineedit_changed signal)
        #check for index coherence
        try:
            index = int(index)
        except:
            index = 1
        index = max(1, index)
        index = min(self.dataframe.shape[0], index)
        #set the correct index without slot evenet
        self.window.lineEdit.textChanged.disconnect(self.loadValue)
        self.window.lineEdit.setText(str(index))
        self.window.lineEdit.textChanged.connect(self.loadValue)
        #create the model for tableview_colums
        model = QtGui.QStandardItemModel()

        #load the value into the dict_trees_import
        self.load_dict_trees_import(index-1)

        #fill the model with dict_trees_import values and import dictionnary
        row = 0
        locality = None        #msg = ''
        for field_name, field_def in self.dict_trees_import.items():
            # if not field_def.get("enabled", True) or not field_def.get("visible", True):
            #     continue
            #clear value_csv and value_dbase
            model.setItem(row, self.column_value, None)
            model.setItem(row, self.column_value+1, None)
            #set the first column (field name)
            item = QtGui.QStandardItem(field_name.capitalize())
            model.setItem(row, 0, item)

            import_value = None

            #check for import dictionnary
            dict_import = field_def.get("import", None)
            if dict_import:
                value = dict_import["column"]
                item = QtGui.QStandardItem(value)
                model.setItem(row, 1, item)
                import_value = self.dict_trees_import[field_name]["import"]["value"]
                if import_value is not None:
                    newitem = QtGui.QStandardItem(str(import_value))
                    #colorize fields with errors
                    # app_style = QtWidgets.QApplication.style()
                    # default_text_color = app_style.standardPalette().color(QtGui.QPalette.Text)
                    # newitem.setForeground(QtGui.QBrush(default_text_color))
                    if dict_import.get("error", 0) > 0:
                        newitem.setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                    elif field_name == "identifier" and import_value in self.dict_identifier_toUpdate:
                        #updating = True
                        locality = self.dict_identifier_toUpdate[import_value][1]
                    model.setItem(row, self.column_value, newitem)
                
            #set the dbase value (column 3)
            dbase_value = self.dict_trees_import[field_name]["value"]
            if dbase_value is not None:
                newitem = QtGui.QStandardItem(str(dbase_value))
                if locality:
                    newitem.setForeground(QtGui.QBrush(QtGui.QColor(100, 100, 255)))
                    #self.dict_trees_import["locality"]["value"] = locality
                model.setItem(row, self.column_value+1, newitem)
                                    
            row +=1
            
        # Add header for columns and set the mdoel
        model.setHorizontalHeaderItem(0, QtGui.QStandardItem("Tree table"))
        model.setHorizontalHeaderItem(1, QtGui.QStandardItem("column"))
        model.setHorizontalHeaderItem(2, QtGui.QStandardItem("Value CSV")) # [" + str(index) + "]"))
        model.setHorizontalHeaderItem(3, QtGui.QStandardItem("Import DB"))
        #set the model in tableview_columns and ajust column sizes
        
        # self.window.label_infos_db.setText(f"{msg}")
        self.window.tblview_columns.setModel(model)
        #self.window.tblview_columns.hideColumn(1)
        self.window.tblview_columns.resizeColumnsToContents()
        header = self.window.tblview_columns.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(self.column_value+1, QHeaderView.Stretch)
                  

    def navigate(self, forward = True):
    #allow to navidate forward (by default) or backward
        current_index = self.window.lineEdit.text()
        if current_index.isdigit():
            current_index = int(current_index)
        else:
            current_index = 1
        if forward:
            current_index += 1
        else:
            current_index -= 1
        self.window.lineEdit.setText(str(current_index))

    def search_nexttError (self):
    #set the value to the next row with error
        self.window.button_search_errors.setEnabled(False)
        self.window.button_search_errors.repaint()
        first = int(self.window.lineEdit.text()) + 1
        while first < self.dataframe.shape[0]:
            if not self.load_dict_trees_import(first-1):
                self.window.lineEdit.setText(str(first))
                break
            first += 1
        self.window.button_search_errors.setEnabled(True)

    def get_id_plot(self):
    #return the id_plot corresponding to the identifier from current dict_trees_import (-1 if not present in the table trees)
        idplot = -1
        try:
            idplot = self.dict_identifier_toUpdate[self.dict_trees_import["identifier"]["value"]][0]
        except:
            _longitude = self.dict_trees_import["longitude"]["value"]
            _latitude = self.dict_trees_import["latitude"]["value"]
            if _longitude and _latitude:
                idplot = 0
        return idplot
    

    def get_table_update (self):
    #return the table update as a list of list of imported values 
    #corresponding to the columns of dict_trees_import + id_plot (= -1 if not found = New occurrence)
        # def get_dict_update_fromIndex(index):
        # #internal function to return the list of values from the current dict_trees_import
        #     self.load_dict_trees_import(index)
        #     list_update = []
        #     for field_def in self.dict_trees_import.values():
        #         value = field_def["value"]
        #         list_update.append(value)
        #     return list_update
        
    #get the table update, all rows imported from the dataframe with corected errors
        dict_update = {}
        self.window.progressBar.setVisible(True)
        self.window.progressBar.setMaximum(self.dataframe.shape[0])
        nb_lines = self.dataframe.shape[0]
        for i in range(nb_lines):
            _tmp = []
            #load the dict_trees_import with the line i
            self.load_dict_trees_import(i)
            idplot = self.get_id_plot()
            if idplot not in dict_update:
                dict_update[idplot] = []            
            for field_def in self.dict_trees_import.values():
                value = field_def["value"]
                _tmp.append(value)
            #add list of imported data to the dict_update with idplot as key (0 :longituteLlatitude, - 1:current plot and >0 identifier found)
            dict_update[idplot].append(_tmp)
            self.window.progressBar.setValue(i)
        self.window.progressBar.setVisible(False)
        return dict_update               
   
    def load_dict_trees_import(self, line_index = 0):
        #import data from the dataframe at the line index
        #set the translated value to each column in self.dict_trees_import
        """ 
            effective translation        
            - month translate input month (text : english, french, spanish and abbreviatins) into an integer (0-12) required by database
            - strata translate strata from integer, or text (english, french, spanish and abbreviatins) to common english term
                special case, if strata.value = 0, the tree is dead and no informations are saved on strata
            - dbh if succession of numeric termes separated by ";"then compute the DBH from the sum of area of each DBH and save the number of stems as the number of terms in the DBH list
                special case, if circumference (or synonyms) are found, then compute the DBH from the circumference
            - flower/fruit, if text (phenology and synonyms), search for commons terms for flower: (cf. flower_reg_pattern and fruit_reg_pattern) and set true or false if found by regex
            - auto-calculate wood_density, leaf_sla, leaf_ldmc if specific fields are included in csv field "leaf_area", "leaf_dry_weight", "leaf_fresh_weight", "leaf_dry_weight"
                "core_length", "core_dry_weight", "core_diameter"        
        """
        #get the line_index in the dataframe to import
        dataline = self.dataframe.iloc[line_index].dropna()
        fix_dead = False
        no_error = True
        tab_stems_dbh = None

        for field_name, field_def in self.dict_trees_import.items():
            import_value = None
            #set the default value first
            field_def["value"] = None
#TODO: allow user to set default value
            # if dict_db_ncpippn[field_name].get("default", None) is not None:
            #     field_def["value"] =  dict_db_tree[field_name]["default"]
#END TODO
            #get the import dictionnary
            dict_import = field_def.get("import", None)
            if not dict_import:
                continue

            ###with a dict_import
            field_csv  = dict_import["column"]
            #set the import value
            if field_csv in dataline:
                import_value = dataline[field_csv]
            dict_import["value"] = import_value
            if field_def["type"] in ['integer', 'numeric']:
                #replace comma by dot (correcting french-english keyboard in string)
                if isinstance(import_value, str):
                    import_value = import_value.replace(",", ".")
                    try:
                        import_value = float(import_value)
                        import_value = int(import_value)
                    except:
                        pass
            #set the import_value (if no import_value, the value is None)
            field_def["value"] = import_value
            #return if not import_value in the field_csv
            if import_value is None:
                continue

            #manage special translation (dbh, fruits/flowers and month)
            field_value = None
            if field_name == 'dbh':
                #test if perimeter
                #isgirth = field_csv in dbh_perimeter_synonyms
                total_area = 0
                #split the values to find multi-stems
                tab_stems_dbh = str(import_value).split(";")
                #compute the sum of area for each stem
                for i in range(len(tab_stems_dbh)):
                    float_dbh = None
                    try:
                        float_dbh = float(tab_stems_dbh[i])
                        if field_csv in dbh_perimeter_synonyms: #compute dbh if value is perimeter
                            float_dbh = float_dbh/mt.pi
                        total_area += mt.pi * (float_dbh/2)**2
                    except:
                        continue
                #compute the resulting DBH from the total area
                field_value = 2*mt.sqrt(total_area/mt.pi)            
            elif field_name in ['flower', 'fruit']:
                #ok if a form of boolean
                if import_value in ['True', 'False', True, False, 1, 0]:
                    field_value = bool(import_value)
                    continue
                elif isinstance (import_value, str): #considering regex search in a str
                    reg_pattern = flower_reg_pattern
                    if field_name == 'fruit':
                        reg_pattern = fruit_reg_pattern
                    field_value = False
                    try:
                        if re.search (reg_pattern, import_value, re.IGNORECASE):
                            field_value = True
                    except:
                        #for debugging
                        print ('error in regex', line_index, import_value, field_value, field_name)
                        field_value = False
            elif field_name in ["month", "strata"]:
                dict_list = dict_strata if field_name == "strata" else dict_month
                #translate month to integer according to dict_month
                try:
                    import_value = int(float(import_value)) #try to translate as an integer
                    if import_value == 0 and field_name == "strata": #tree is considered as dead
                        fix_dead = True
                except:
                    import_value = import_value.lower()
                #search for translation through dict_synonyms
                if import_value in dict_list:
                    field_value = import_value
                else:
                    for key, list_value in dict_list.items():
                        if import_value in list_value:
                            field_value = key
                            break
                #if field_value is str (item), capitalize:
                if isinstance(field_value, str):
                    field_value = field_value.capitalize()
            else:
                field_value = import_value

            #delete error code if any
            if "error" in dict_import:
                del dict_import["error"]
            #set the final value
            field_def["value"] = None            
            if field_value:
                #save typed value (as in table, none if not typed and error code add to dict_import definition)
                try:
                    field_def["value"] = get_typed_value(field_name, field_value)
                except ValueError as err:
                    field_def["value"] = None
                    dict_import["error"] = err.args[1]
                    no_error = False

    #actions link to the overall dict_trees_import
        #test for longitude/latitude validity, None to location if invalid
        try:
            _test = self.dict_trees_import["longitude"]["value"]  * self.dict_trees_import["latitude"]["value"]
        except:
            self.dict_trees_import["longitude"]["value"] = None
            self.dict_trees_import["latitude"]["value"] = None
            self.dict_trees_import["locality"]["value"] = None
        # id_plot = self.get_id_plot()
        # if id_plot > 0:
        #     self.dict_trees_import["locality"]["value"] = self.dict_identifier_toUpdate[self.dict_trees_import["identifier"]["value"]][1]
        # elif id_plot < 0:
        #     self.dict_trees_import["locality"]["value"] = dict_db_plot["locality"]["value"]
        #set the stems number according to the len of tab_stems_dbh
        #excepting if 1 stems in tab_stems_dbh and _stems >=0
        if tab_stems_dbh:
            _stems = self.dict_trees_import["stems"]["value"]
            if len(tab_stems_dbh) == 1 and not _stems:
                _stems = 1
            elif len(tab_stems_dbh) > 1:
                _stems = len(tab_stems_dbh)
            self.dict_trees_import["stems"]["value"] = int(_stems)

        #set to dead if strata = 0
        if fix_dead:
            self.dict_trees_import["dead"]["value"] = True
            self.dict_trees_import["strata"]["value"] = None

        #set auto-calculate columns (leaf_sla, leaf_ldmc, wood_density), if raw data are available in dataline
        #Try to calculate leaf_sla from leaf_area and leaf_dry_weight
        try:
            leaf_area = self.dict_trees_import["leaf_area"]["value"]
            leaf_sla = leaf_area / float(dataline["leaf_dry_weight"])
            decimal = self.dict_trees_import["leaf_sla"].get("decimal", PLOT_DEFAULT_DECIMAL)
            self.dict_trees_import["leaf_sla"]["value"] = round(leaf_sla, decimal)
        except:
            pass
        #Try to calculate leaf_ldmc from leaf_fresh_weight and leaf_dry_weight
        # terms_tosearch = ["leaf_fresh_weight", "leaf_dry_weight"]
        # if all(term in self.type_columns for term in terms_tosearch):
        try:
            leaf_ldmc = float(dataline["leaf_dry_weight"])/ float(dataline["leaf_fresh_weight"])
            decimal = self.dict_trees_import["leaf_ldmc"].get("decimal", PLOT_DEFAULT_DECIMAL)
            self.dict_trees_import["leaf_ldmc"]["value"] = round(leaf_ldmc,decimal)
        except:
            pass
        #Try to calculate wood_density from core_dry_weight, core_diameter and core_length
        # terms_tosearch = ["core_length", "core_dry_weight", "core_diameter"]
        # if all(term in self.type_columns for term in terms_tosearch):
        try:
            core_volume = mt.pi * ((float(dataline["core_diameter"])/2) ** 2)* float(dataline["core_length"]) * 0.1
            wood_density = float(dataline["core_dry_weight"])/ core_volume
            decimal = self.dict_trees_import["wood_density"].get("decimal", PLOT_DEFAULT_DECIMAL)
            self.dict_trees_import["wood_density"]["value"] = round(wood_density,decimal)
        except:
            pass
        return no_error

    def show_modal(self):
        self.window.exec_()
        
    def close(self):
        self.window.close()       
    
    def validate (self):
        def on_cancel_clicked():
        #cancel transaction
            win_preview.close()
            
        def updateChildItems(item):
            state = item.checkState()
            for row in range(item.rowCount()):
                child = item.child(row)
                if child.isCheckable():
                    child.setCheckState(state)

        def onItemChanged(item):
            if item.isCheckable():
                updateChildItems(item)

        def on_ok_clicked():
        #validate update and insert occurrences from the Preview Updater
            #create a list of exclude id_plot for inserting or updating (add id_plot from unchecked item.data())
            tab_insert_exclude_idplot = [] 
            tab_update_exclude_idplot  = []
            # try:
            #     if item_insert[0].checkState() == 0:
            #         tab_insert_exclude_idplot.append (-1)
            # except:
            #     pass
            # try:
            #     if item_point[0].checkState() == 0:
            #         tab_insert_exclude_idplot.append (0)
            # except:
            #     pass
            for row in range(item_insert.rowCount()):
                if item_insert.child(row, 0).checkState() == 0:
                    tab_insert_exclude_idplot.append (item_insert.child(row, 0).index().data(Qt.UserRole))
            for row in range(item_update.rowCount()):
                if item_update.child(row, 0).checkState() == 0:
                    tab_update_exclude_idplot.append (item_update.child(row, 0).index().data(Qt.UserRole))
        
            #read the items value in table_imported_csv to create sql statement
            list_toUpdate = []
            list_toInsert = []
            list_points = []
            index_locality = column_indexes["locality"]
            index_longitude = column_indexes["longitude"]
            index_latitude = column_indexes["latitude"]
            for idplot, ls_list_update in dict_imported_csv.items():

                #test for exclusion of unchecked id_plot (cf. model, previously checked)
                if idplot <= 0 and idplot in tab_insert_exclude_idplot:
                    continue
                elif idplot in tab_update_exclude_idplot:
                    continue

                for list_update in ls_list_update:
                    
                    #check values for dbase compatibility (NULL/None and Text), and create list of sql statement
                    row = 0
                    _tmp =[]
                    _tabcolumn = []
                    _tabvalue = []
                    identifier = list_update[index_identifier]
                    for value in list_update:
                        if value:
                            field_name = tab_column[row]
                            str_value = get_str_value(value)
                            if row in tab_index_text: #columns cast as text (cf. previous)
                                str_value = "'" + str_value + "'"
                            #set the correct value to the list
                            list_update[row] = str_value
                            #do not include identifier and fields not in table trees in the update statement
                            if field_name in column_trees:
                                _tabcolumn.append(field_name)
                                _tabvalue.append(str_value)
                                if row != index_identifier:
                                    _tmp.append (field_name + " = " + str_value)
                        row += 1
                    if _tmp and identifier and idplot > 0:
                        sql_query =  f"UPDATE {DBASE_SCHEMA_TREES} SET {', '.join(_tmp)} WHERE identifier = '{identifier}' AND id_plot = {idplot};"
                        list_toUpdate.append(sql_query)
                    elif _tabvalue:
                        if idplot == 0: #new point, (longitude & latitude and no identifier or not in the current table trees)
                            latitude = list_update[index_latitude]
                            longitude = list_update[index_longitude]
                            locality = list_update[index_locality]
                            if not locality:
                                locality = current_locality
                            else:
                                locality = locality.strip("'")
                            #create a couple of query, first try to insert a new plot (nothing if conflict) and then select plot
                            sql_toInsert = f"""
                            INSERT INTO {DBASE_SCHEMA_PLOTS} (collection, locality, longitude, latitude, type)
                            VALUES ('{current_collection}', '{locality}', {longitude}, {latitude}, 'Point')
                            ON CONFLICT DO NOTHING;
                            INSERT INTO {DBASE_SCHEMA_TREES} (id_plot, {', '.join(_tabcolumn)})
                            SELECT id_plot, {', '.join(_tabvalue)}
                            FROM {DBASE_SCHEMA_PLOTS}
                            WHERE longitude = {longitude} AND latitude = {latitude} AND type = 'Point';
                            """
                            list_points.append(sql_toInsert)
                        else:
                            sql_toInsert = f"""
                            INSERT INTO {DBASE_SCHEMA_TREES} (id_plot, {', '.join(_tabcolumn)})
                            VALUES ({str(idplot)}, {', '.join(_tabvalue)})
                            ON CONFLICT (identifier) DO NOTHING RETURNING identifier;
                            """          
                            list_toInsert.append (sql_toInsert)
                    # list_update[-1:] = [str(id_plot)]
                    # list_toInsert.append ("\n(" + ', '.join(list_update) + ")")

        #execute query
            sql_toInsert =''
            self.rows_imported = 0
            if list_points:
                sql_toInsert = "\n".join(list_points)
                self.rows_imported += len(list_points)
                print (sql_toInsert)
                #database_execute_query(sql_toInsert)
            if list_toInsert:
                sql_toInsert = "\n".join(list_toInsert)
                self.rows_imported += len(list_toInsert)
                print (sql_toInsert)
                #database_execute_query(sql_toInsert)
            if list_toUpdate:
                sql_toInsert = "\n".join(list_toUpdate)
                self.rows_imported += len(list_toInsert)
                print (sql_toInsert)
                #database_execute_query(sql_toInsert)
            win_preview.close()
            self.close()
            
    #Begining of the core function
        self.buttonOK = True
        tab_index_text = []
        tab_column = []
        #ls_count_byplot = {}
        index_identifier = -1
        #index_longitude = -1
        #index_latitude = -1
        column_indexes = {}
        column_trees = {}
        current_collection = dict_db_plot["collection"]["value"]
        current_locality = dict_db_plot["locality"]["value"]
        current_plot = dict_db_plot["plot"]["value"]

        #get id_plot for importation of new trees (selected value in dbase)
        id_plot = dict_db_plot["id_plot"]["value"]
        
        row = 0
        #get index of columns to casted as text type (for quick access in next loop)
        for field_name, field_def in self.dict_trees_import.items():
            #create a tab_index, a list of index of columns to casted as text type in the next loop
            tab_column.append(field_name)
            column_indexes[field_name] = row
            if field_name in dict_db_tree:
                column_trees[field_name] = row
            if field_def["type"] in ["text", "memo"]:
                tab_index_text.append(row)
            if field_name == "identifier": 
                index_identifier = row
            # if field_name == "longitude":
            #     index_longitude = row
            # if field_name == "latitude":
            #     index_latitude = row
            row += 1
        #add the column id_plot add by self.get_table_update() at the end of the returned lists
        # tab_column.append("id_plot")
        # index_idplot = len(tab_column) - 1
        #get the dictionnary of imported data by plot (0 = New Point (longitude/latitude) - 1 : new occurrrences in current plot and other existing plots)
        dict_imported_csv = self.get_table_update()
        #read the items value in any table_update list and translate into sql_statement
        #each list contains the value relative to dict_import + id_plot as the last row of any each list
        #(id_plot = - 1, add to current plot, = 0 insert new points wirth long/lat and >=0 for updating a current identifier found in id_plot
        #table_imported_csv = self.get_table_update()

        #create a dictionnary of id_plot with the total number of occurrences by plot (including 0 and -1)
        # for list_update in table_imported_csv:
        #     row = 0
        #     #counter to row by idplot (the last column = id_plot)
        #     idplot = list_update[-1]
        #     if not idplot in ls_count_byplot:
        #         ls_count_byplot[idplot] = 1
        #     else:
        #         ls_count_byplot[idplot] += 1    

#manage preview of updating and adding trees
    #load a query to get details on plots
        list_str_idplot = [str(key) for key in dict_imported_csv.keys() if key > 0]
        #create the sql_satement of found plots for display
        sql_query = f"""
                        SELECT '{current_collection}' as collection, '{current_locality}' as locality, NULL AS plot, 0 AS id_plot
                        FROM {DBASE_SCHEMA_PLOTS}
                        UNION
                        SELECT '{current_collection}' as collection, '{current_locality}' as locality, NULL AS plot, -1 AS id_plot
                        FROM {DBASE_SCHEMA_PLOTS}
                        UNION
                        SELECT collection, locality, plot, id_plot
                        FROM {DBASE_SCHEMA_PLOTS}
                        WHERE id_plot IN ({", ".join(list_str_idplot)})
                        ORDER BY plot, locality, collection
                    """        
        
        query = QtSql.QSqlQuery(sql_query)
        #load the model for treeview            
        tab_header = ["Plot", "Locality", "Collection", "Count"]
        model = QtGui.QStandardItemModel()
        model.setHorizontalHeaderLabels(tab_header)
        model.setColumnCount(4)
        font = QtGui.QFont()
        font.setBold(True)
        
        #create the three root nodes
        #nodes for new inventory points (idplot = 0)
        #tab_adding = dict_imported_csv.get(0, [])
        # item_point = [QtGui.QStandardItem("Adding inventory points"), None, None, QtGui.QStandardItem(str(len(tab_adding)))]
        # item_point[0].setFont(font)
        # model.appendRow(item_point)

        #nodes for new occurrences in current plot (idplot = -1)
        #tab_inserted = dict_imported_csv.get(-1, [])
        item_insert = QtGui.QStandardItem("Adding occurrences") ##,None, None, QtGui.QStandardItem(str(len(tab_inserted)+len(tab_adding)))]
        item_insert.setFont(font)
        item_insert.setCheckable(True)
        item_insert.setCheckState(QtCore.Qt.Checked)
        model.appendRow(item_insert)
            
        #nodes for new occurrences other plots (idplot >0)
        item_update = QtGui.QStandardItem("Updating occurrences")
        item_update.setFont(font)
        item_update.setCheckable(True)
        item_update.setCheckState(QtCore.Qt.Checked)
        model.appendRow(item_update)

        #browse the query result and add result if some
        total_updated = 0
        total_inserted = 0
        while query.next():
            id_plot = query.value("id_plot")
            ls_imported = dict_imported_csv.get(id_plot, None)
            if not ls_imported:
                continue
            count = len(ls_imported)
            if id_plot == 0:
                    item = [
                                QtGui.QStandardItem("Inventory points"),None, None,
                                QtGui.QStandardItem(str(count))
                            ]
                    item_insert.appendRow(item)
                    total_inserted += count
                    #item = item_point
            else:
                if id_plot > 0:
                    item = [
                                QtGui.QStandardItem(query.value("plot")),
                                QtGui.QStandardItem(query.value("locality")),
                                QtGui.QStandardItem(query.value("collection")),
                                QtGui.QStandardItem(str(count))
                            ]
                    total_updated += count
                    item_update.appendRow(item)
                else:
                    item = [
                                QtGui.QStandardItem(current_plot),
                                QtGui.QStandardItem(current_locality),
                                QtGui.QStandardItem(current_collection),
                                QtGui.QStandardItem(str(count))
                            ]
                    total_inserted += count
                    item_insert.appendRow(item)

            #set the id_plot to the parent item
            item[0].setCheckable(True)
            item[0].setCheckState(QtCore.Qt.Checked)  
            item[0].setData(id_plot, role=Qt.UserRole)
            #append the child rows to item
            for row in dict_imported_csv[id_plot]:
                row_item = [QtGui.QStandardItem(str(row[index_identifier]))]
                if id_plot == 0:
                    locality = row[column_indexes["locality"]]
                    if not locality:
                        locality = current_locality
                    row_item.append(QtGui.QStandardItem(str(locality)))
                    row_item.append(QtGui.QStandardItem(current_collection)) 
                item[0].appendRow (row_item)
        #set the total account of updated row
        model.setItem(item_update.row(), 3, QtGui.QStandardItem(str(total_updated)))
        model.setItem(item_insert.row(), 3, QtGui.QStandardItem(str(total_inserted)))
        


        #load UI for preview and fill the treeview
        win_preview = uic.loadUi('pn_update_preview.ui')
        win_preview.buttonBox.accepted.connect(on_ok_clicked)
        win_preview.buttonBox.rejected.connect(on_cancel_clicked)
        trview_result = win_preview.trView_preview
        trview_result.setModel(model)
        model.itemChanged.connect(onItemChanged)
        #trview_result.setExpanded(item_update.index(), True)
        # trview_result.setExpanded(item_insert.index(), True)
        for column in range(model.columnCount()):
                trview_result.resizeColumnToContents(column)
        # Stretch the first column
        trview_result.header().setStretchLastSection(False)
        trview_result.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        #open the preview
        win_preview.exec_()


###MAIN WINDOWS
#class delegate for editing in tableviews (tree and plot)
class CustomDelegate(QStyledItemDelegate):
    dataChanged = pyqtSignal(str, object)  # Signal after data is changed
    textUpdated = pyqtSignal(str, object)  # Signal during text edition
    def __init__(self, parent=None):
        super().__init__(parent)
        self.valid = False
        self.table_def = dict_db_ncpippn
        self.currentIndex = None
        self.text_editor = None
        
        #self.exclude_columns = [key for key, value in self.table_def.items() if not value.get('enabled', True)]

    def get_header (self, index):
        #return the lower case name in the column 0
        row = index.row()
        return index.sibling(row, 0).data(Qt.DisplayRole).lower()
    def is_enabled(self, index):
        header = self.get_header (index)
        return self.table_def[header].get('enabled', True)

    def paint(self, painter, option, index):
        # Paint row according to excluded columns
        #header = self.get_header (index)
        #enabled = self.table_def[header].get('enabled', True)
        if not self.is_enabled(index): #and not enabled: #header in self.exclude_columns:
            option = QStyleOptionViewItem(option)
            self.initStyleOption(option, index)
            option.palette.setColor(QtGui.QPalette.Text, QtGui.QColor(120, 120, 120))  # Couleur grise pour le texte
            font = QtGui.QFont()
            font.setItalic(True)
            font.setPointSize(9)
            option.font = font
            super().paint(painter, option, index)        
        else:
            super().paint(painter, option, index)
    
    def handle_event (self):
        self.valid = True
        if not isinstance (self.text_editor, QLineEdit):
            return
        try:
            header = self.get_header (self.currentIndex)
            value = self.text_editor.text()
            self.textUpdated.emit(header, value)
        except:
            return

        

    def createEditor(self, parent, option, index):
        self.valid = False
        self.currentIndex = index
        self.text_editor = None

        header = self.get_header (index)
        if index.column() == 0 or not self.is_enabled(index): #header in self.exclude_columns:
            return None
    #get the field definition
        field_def = self.table_def.get(header, {})
        if not field_def:
            return
    
    #create editor according to the field type
        if field_def["type"] == 'boolean':
            return
        elif "items" in field_def:
            editor = QComboBox(parent)
            editor.addItems(field_def["items"])
            if field_def.get("editable", False):
                editor.setEditable(True)
                editor.lineEdit().setFont (editor.font())
        elif field_def["type"] == 'integer':
            editor = QSpinBox(parent)
            editor.setSingleStep(1)
            if "min" in field_def:
                editor.setMinimum(field_def["min"])
            if "max" in field_def:
                editor.setMaximum(field_def["max"])
        elif field_def["type"] == 'numeric':
            editor = QDoubleSpinBox(parent)
            editor.setMaximum(float(1E6))
            
            decimals = field_def.get("decimal", PLOT_DEFAULT_DECIMAL)
            if decimals <= 2:
                editor.setSingleStep(1)
            else:
                editor.setSingleStep(0.1)

            editor.setDecimals(decimals)
            if "min" in field_def:
                editor.setMinimum(field_def["min"])                               
            if "max" in field_def:
                editor.setMaximum(field_def["max"]) 
        elif field_def["type"] == 'memo':
            editor = QTextEdit(parent)
            editor.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        else:
            editor = QLineEdit(parent)
            editor.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.text_editor = editor

    #set the tooltip            
        _tip = field_def.get("tip", header)
        if "unit" in field_def:
            _unit = field_def["unit"]
            _tip += " (" + _unit + ")"
        if _tip != header:
            editor.setToolTip (_tip)            
    #set the slot events
        #     self.valid = True
        # return editor
        if isinstance (editor, (QDoubleSpinBox, QSpinBox)):
            editor.valueChanged.connect(self.handle_event)
        elif isinstance (editor, QComboBox):
            editor.activated.connect(self.handle_event)
        else:
            editor.textChanged.connect(self.handle_event)
        return editor


    def setEditorData(self, editor, index):
        value = index.data(Qt.EditRole)
        value = get_str_value(value)
        try:
            if isinstance(editor, QComboBox):
                if isinstance(value, int):
                    editor.setCurrentIndex(value)
                else:
                    editor.setCurrentText(value)
            elif isinstance(editor, QSpinBox):
                editor.setValue(int(value))
            elif isinstance(editor, QDoubleSpinBox):
                if len(value) > 0:
                    value = float(str(value).replace(",", "."))
                    editor.setValue(float(value))
            else:
                editor.setText(str(value))
        except:
            pass

    def setModelData(self, editor, model, index):
        if not self.valid : 
            return
        header = self.get_header (index)
        #get the field definition
        field_def = self.table_def.get(header, {})
        if not field_def:
            return
        #check for value, do not alter the model, emit signal dataChanged
        if isinstance(editor, QComboBox):
            if editor.currentText() == "":
                value = None
            elif field_def["type"] in ['integer', 'numeric']:
                value = editor.currentIndex()
            else:
                value = editor.currentText()
        elif isinstance(editor, QSpinBox):
            value = int(editor.value())
        elif isinstance(editor, QDoubleSpinBox):
            decimals = field_def.get("decimal", PLOT_DEFAULT_DECIMAL)
            value = round(float(editor.value()), decimals)
        elif isinstance(editor, QTextEdit):
            value = editor.toPlainText()
        else:
            value = editor.text()
        self.dataChanged.emit(header, value)
        #model.setData(index, value, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


# class ShapeDelegate(QStyledItemDelegate):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         # Définir les formes et couleurs directement ici
#         self.shapes_colors = [
#             ("circle", QtGui.QColor(Qt.green)),
#             ("square", QtGui.QColor(Qt.red))
#         ]
#     def paint(self, painter, option, index):
#         # Appel de la méthode paint() de la classe parente pour peindre le fond, le texte, etc.
#         super().paint(painter, option, index)

#         # Si l'item est valide
#         if index.isValid():
#             # Dessiner chaque forme avec sa couleur spécifiée
#             for shape, color in self.shapes_colors:
#                 painter.setBrush(color)
#                 if shape == "circle":
#                     diameter = 10  # Diamètre du cercle
#                     x = option.rect.x() + 10  # Position horizontale du cercle
#                     y = option.rect.y() + (option.rect.height() - diameter) / 2  # Position verticale du cercle
#                     ellipse_rect = QRectF(x, y, diameter, diameter)
#                     painter.drawEllipse(ellipse_rect)
#                 elif shape == "square":
#                     side_length = 10  # Longueur du côté du carré
#                     x = option.rect.x() + 30  # Position horizontale du carré (pour le décaler)
#                     y = option.rect.y() + (option.rect.height() - side_length) / 2  # Position verticale du carré
#                     square_rect = QRectF(x, y, side_length, side_length)
#                     painter.drawRect(square_rect)


# class NCPIPPN_tree_model(QtCore.QAbstractTableModel):
# #to manage a specific model for display data as a list
# # include red/green dots considering the last field of the list as boolean (green if True)
# # include a specific font attributes for columns include in header_filtered
# # receive a list (data) 
#     def __init__(self, data = None):
#         super(NCPIPPN_tree_model, self).__init__()
#         self._data = []
#         self._data = data if data != None else []
#         self.header_labels = []
#         self.header_filtered = []

#     def getdata(self, with_header = False):
#     #get data, ingore the last field (= valid)
#         data = []
#         if with_header:
#             data.append(self.header_labels[:-1])
#         for row in self._data:
#             data.append([get_str_value(item) for item in row[:-1]])
#         return data
    
#     def resetdata(self, newdata = None):
#         self.beginResetModel()
#         self._data = newdata if newdata != None else []
#         self.endResetModel()
#     def get_idtree (self, row):
#         try:
#             return self._data[row][self.columnCount()+1]
#         except:
#             return None

#     def get_idplot (self, row):
#         try:
#             return self._data[row][self.columnCount()+2]
#         except:
#             return None
        
#     def headerData(self, section, orientation = Qt.Horizontal, role = Qt.DisplayRole):
#         if len(self.header_labels) == 0:return
#         if role == Qt.DisplayRole and orientation == Qt.Horizontal:
#             return  self.header_labels[section]
#         #change font attributes if a field is include in header_filtered
#         if role == Qt.FontRole and orientation == Qt.Horizontal:
#             if section in self.header_filtered:
#                 f = QtGui.QFont()
#                 f.setBold(True)
#                 f.setUnderline(True)
#                 f.setItalic(True)
#                 return f

#     def data(self, index, role):
#         if not index.isValid():
#             return None
#         if 0 <= index.row() < self.rowCount():
#             item = self._data[index.row()]
#             col = index.column()
#             if role == Qt.DisplayRole:
#                     return self._data[index.row()][index.column()]
#             elif role == Qt.UserRole:
#                 return item
#             elif role == Qt.DecorationRole:
#                 if col == 0:
#                     #idtaxonref = getattr(item, 'stid_taxon_ref', 0)
#                     colour = QtGui.QColor(255,0,0,255)
#                     if self._data[index.row()][self.columnCount()]==True:
#                         colour = QtGui.QColor(0,255,0,255)
#                     px = QtGui.QPixmap(13,13)
#                     px.fill(QtCore.Qt.transparent)
#                     painter = QtGui.QPainter(px)
#                     painter.setRenderHint(QtGui.QPainter.Antialiasing)
#                     px_size = px.rect().adjusted(2,2,-2,-2)
#                     painter.setBrush(colour)
#                     painter.setPen(QtGui.QPen(QtCore.Qt.black, 1,
#                         QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin))
#                     #painter.drawEllipse(px_size)
#                     painter.drawRect(px_size)
#                     painter.end()
#                     return QtGui.QIcon(px)

#     def rowCount(self, index=QtCore.QModelIndex()):
#         return len(self._data)

#     def columnCount(self, index=QtCore.QModelIndex()):
#         try:
#             return len(self._data[0])-3
#         except:
#             return 0
        
#     # def addItem (self, clrowtable):
#     #     self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
#     #     self._data.append(clrowtable)
#     #     self.endInsertRows()


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()


        self.dict_user_plot = copy.deepcopy(dict_db_plot)
        self.dict_user_tree = copy.deepcopy(dict_db_tree)
        self.current_collection = None

        # load the GUI
        self.ui = uic.loadUi("plots.ui")

        #add statusBar
        self.statusLabel = QLabel('Select a Collection', self)
        
        frame = QFrame(self)
        frame.setStyleSheet("background-color: transparent;")
        self.statusIndicator = QWidget(frame)
        self.statusIndicator.setFixedSize(10, 10)
        self.statusConnection = QLabel(None, frame)
        self.statusIndicator.setStyleSheet("background-color: transparent;")
        self.statusConnection.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        frame_layout = QHBoxLayout(frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)

        export_button = QPushButton()
        export_button.setText("Export data")
        # export_button.setToolButtonStyle(Qt.ToolButtonTextOnly)
        # export_button.setPopupMode(QToolButton.InstantPopup)

        export_menu = QMenu()
        menu_items = ["Plots", "Trees", "Taxa", "Occurrences"]
        for item in menu_items:
            action = QAction(item, self)
            action.triggered.connect(lambda checked, item=item: self.export_menu(item.lower()))
            export_menu.addAction(action)
        export_button.setMenu(export_menu)
        frame_layout.addWidget(export_button)
        self.ui.statusBar().addWidget(self.statusLabel)

        frame_layout.addWidget(self.statusIndicator)
        frame_layout.addWidget(self.statusIndicator)
        frame_layout.addWidget(self.statusConnection)       
        self.ui.statusBar().addPermanentWidget(frame)

        #add new/delete button to buttonBox_tree
        self.button_apply_tree = self.ui.buttonBox_tree.button(QDialogButtonBox.Apply)
        self.button_cancel_tree = self.ui.buttonBox_tree.button(QDialogButtonBox.Cancel)
        self.button_new_tree = QPushButton("New")
        self.button_new_tree.setIcon(QtGui.QIcon.fromTheme("document-new"))
        self.button_delete_tree = QPushButton("Delete")
        self.button_delete_tree.setIcon(QtGui.QIcon.fromTheme("edit-delete"))

        #add new/delete button on buttonBox_plot
        self.button_apply_plot = self.ui.buttonBox_plot.button(QDialogButtonBox.Apply)
        self.button_cancel_plot = self.ui.buttonBox_plot.button(QDialogButtonBox.Cancel)
        self.button_new_plot = QPushButton("New")
        self.button_new_plot.setIcon(QtGui.QIcon.fromTheme("document-new"))
        self.button_delete_plot = QPushButton("Delete")
        self.button_delete_plot.setIcon(QtGui.QIcon.fromTheme("edit-delete"))

        #set disabled by default
        self.button_apply_tree.setEnabled(False)
        self.button_new_tree.setEnabled(False)
        self.button_new_plot.setEnabled(False)
        self.button_cancel_tree.setEnabled(False)
        self.button_delete_tree.setEnabled(False)
        self.button_apply_plot.setEnabled(False)
        self.button_cancel_plot.setEnabled(False)
        self.button_delete_plot.setEnabled(False)
        self.ui.frame_history_slider.setVisible(False)

        #add buttons to buttonBox
        self.ui.buttonBox_tree.addButton(self.button_new_tree, QDialogButtonBox.ActionRole)
        self.ui.buttonBox_tree.addButton(self.button_delete_tree, QDialogButtonBox.ActionRole)
        self.ui.buttonBox_plot.addButton(self.button_new_plot, QDialogButtonBox.ActionRole)
        self.ui.buttonBox_plot.addButton(self.button_delete_plot, QDialogButtonBox.ActionRole)

        #open database
        dbopen = False
        import configparser
        config = configparser.ConfigParser()
        file_config = config.read('config.ini')
        section = 'database'
        self.statusIndicator.setStyleSheet("background-color: rgb(255, 0, 0); border-radius: 5px;")
        self.statusConnection.setText("Not Connected")
        if file_config and section in config.sections():
            db = QtSql.QSqlDatabase.addDatabase("QPSQL")
            db.setHostName(config['database']['host'])
            db.setUserName(config['database']['user'])
            db.setPassword(config['database']['password'])
            db.setDatabaseName(config['database']['database'])
            if db.open():
                dbopen = True
                default_db_name = QtSql.QSqlDatabase.database().databaseName()
                self.statusIndicator.setStyleSheet("background-color: rgb(0, 255, 0); border-radius: 5px;")
                self.statusConnection.setText("Connected : "+ default_db_name)
        #return if not open
        if not dbopen:
            return       

        #if open
        #connect slot to function event
        self.button_new_plot.clicked.connect(self.button_new_plot_click)
        self.button_new_tree.clicked.connect(self.button_new_tree_click)
        self.button_apply_tree.clicked.connect(self.button_apply_tree_click)
        self.button_apply_plot.clicked.connect(self.button_apply_plot_click)
        self.button_delete_tree.clicked.connect(self.button_delete_tree_click)
        self.button_delete_plot.clicked.connect(self.button_delete_plot_click)
        self.button_cancel_tree.clicked.connect(self.button_cancel_tree_click)
        self.button_cancel_plot.clicked.connect(self.button_cancel_plot_click)
        self.ui.comboBox_collections.currentIndexChanged.connect(self.load_collections)
        self.ui.comboBox_types.activated.connect(self.load_plots)
        self.ui.filter_button_dead.toggled.connect(self.load_trees)
        self.ui.filter_button_trait.toggled.connect(self.load_trees)
        self.ui.filter_button_fruit.toggled.connect(self.load_trees)
        self.ui.filter_button_flower.toggled.connect(self.load_trees)
        self.ui.filter_button_allometry.toggled.connect(self.load_trees)
        self.ui.button_replace_taxa.clicked.connect(self.replace_taxanames)
        self.ui.button_add_synonym.clicked.connect(self.add_synonym)
        self.ui.slider_history.valueChanged.connect(self.slider_history_seturrentIndex)
        self.ui.lineEdit_search_taxa.textChanged.connect(self.load_taxa_search)
        self.ui.treeview_scoretaxa.doubleClicked.connect(self.treeview_scoretaxa_dbleClicked)
        self.ui.button_import_trees.clicked.connect(self.button_import_trees_click)

        # set the editors delegate to Qtableview(s)
        self.delegate = CustomDelegate()
        self.ui.tableView_tree.setItemDelegate(self.delegate)
        self.ui.tableView_plot.setItemDelegate(self.delegate)
        self.delegate.dataChanged.connect(self.data_changed)
        self.delegate.textUpdated.connect(self.text_changed)

        #set the dragdrop
        self.ui.tableView_plots.setDragEnabled(True)
        self.ui.treeView_collections.setAcceptDrops(True)
        self.ui.treeView_collections.dropEvent = self.treeView_collections_dropEvent
        self.ui.treeView_collections.dragEnterEvent = self.treeView_collections_dragEnterEvent
        self.ui.tableView_trees.setDragEnabled(True)
        self.ui.tableView_plots.setAcceptDrops(True)
        self.ui.tableView_plots.dropEvent = self.tableview_plots_dropEvent

        #execute a selection on combobox collections
        self.button_new_plot.setEnabled(True)
        self.ui.comboBox_collections.setCurrentIndex(0)

    def export_menu(self, item):
        import csv
        #set parameters to QfileDialog
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        #options |= QFileDialog.DontUseNativeDialog
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Fichiers CSV (*.csv)")
        file_dialog.setDefaultSuffix("csv")
        file_name, _ = file_dialog.getSaveFileName(
            None, "Export to CSV File", "", "CSV Files (*.csv);;All files (*)", options=options)
        #exit of no file name
        if not file_name:
            return
        
        #check for csv extension
        if not file_name.lower().endswith(".csv"):
            file_name += ".csv"
        delimiter = ';'



    #export either plots, trees, taxa and occurrences
        sql = ""
        data = []
        if item == 'plots':
            sql = f"SELECT * FROM {DBASE_SCHEMA_PLOTS} ORDER BY plot"
        elif item == 'taxa':
            data = self.ui.tblView_resolution.model().getdata(True)        
        elif item in  ('trees', 'occurrences'):
            ls_trees_fields = []
            for column, value in dict_db_tree.items():
                if value.get('enabled', True):
                    ls_trees_fields.append("a." + column)
            if item == 'occurrences':
                for column, value in dict_db_plot.items():
                    if value.get('enabled', True) and column not in ('radius'):
                        ls_trees_fields.append("b." + column)
            sql = f"""
                    WITH query AS 
                        (SELECT {','.join(ls_trees_fields)}, b.id_plot, a.id_tree
                        FROM
                        {DBASE_SCHEMA_TREES} a
                        INNER JOIN {DBASE_SCHEMA_PLOTS} b ON a.id_plot = b.id_plot
                        {self.get_trees_sql_where()}
                        ORDER BY taxaname)
                    SELECT b.taxonref, a.*, b.id_taxonref AS id_taxa
                    FROM query a
                    LEFT JOIN {DBASE_SCHEMA_TAXONOMY}.pn_taxa_searchnames (array(select DISTINCT taxaname::TEXT from query)) b
                    ON a.taxaname = b.original_name
                    ORDER BY identifier
                """
        if sql:
            print (sql)
            query = QtSql.QSqlQuery(sql)
            if query.isActive():
                record = query.record()
                data.append([record.fieldName(x) for x in range(record.count())])
                while query.next():
                    _data = []
                    for x in range(record.count()-1):
                        _value = get_str_value(query.value(record.fieldName(x)))
                        if delimiter in _value:
                            _value = '"' + _value + '"'
                        _data.append(_value)
                    data.append(_data)
                #write the data
        with open(file_name, "w", newline="") as file:
            writer = csv.writer(file, delimiter=delimiter, skipinitialspace = True, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(data)
                

    def set_dict_dbase(self, id, table):
        print ("set_dict_dbase",table, id)
    #fill the dict_dbase (tree or plot) from database and reload the dict_user (plot or tree)
        if table == 'plots':
            sql_select = f"SELECT * FROM {DBASE_SCHEMA_PLOTS} WHERE id_plot = {id}"
            dict_user = dict_db_plot
        elif table == 'trees':
            #list of fields
            ls_fields = []
            for dbcolumn, field_def in dict_db_tree.items():
                if dbcolumn not in ["history"]:
                    ls_fields.append(dbcolumn)
            sql_fields = ", ".join(ls_fields)
            sql_select = f"SELECT {sql_fields} FROM {DBASE_SCHEMA_TREES} WHERE id_tree = {id} UNION "
            sql_select += f"SELECT {sql_fields} FROM {DBASE_SCHEMA_TREES}_history WHERE id_tree = {id}"
            sql_select += "\nORDER BY time_updated DESC"
            dict_user = dict_db_tree
            dict_db_tree["history"]["items"] = []
            dict_db_tree["history"]["value"] = 0
        else:
            return
        #set the dictionnary values to None
        for dbcolumn, field_def in dict_user.items():
            field_def["value"] = None
        #if id, set data from the sql query (including historical data for trees)
        list_db_tree_history = []
        if id:
            #play the query and set the data to dict_user
            query = QtSql.QSqlQuery(sql_select)
            _tmp = dict_user
            while query.next():
                for dbcolumn in _tmp.keys():
                    value = None
                    try:
                        if query.record().indexOf(dbcolumn) != -1:
                            if not query.isNull(dbcolumn):
                                value = query.value(dbcolumn)
                            _tmp[dbcolumn]["value"] = value
                    except:
                        pass
                #in case of plots, only one row is returned
                #in case of trees, the next rows come from tree history
                list_db_tree_history.append(_tmp)
                _tmp = copy.deepcopy(dict_db_tree)
                    #elf.load_tree_history()
        elif table == 'trees':
            #new tree, set the default values
            dict_user["dead"]["value"] = False
            dict_user["month"]["value"] = datetime.now().month        
            dict_user["year"]["value"] = datetime.now().year
        elif table == 'plots':
            #new plot, set the default values
            for key in ["collection", "locality", "type", "width", "length", "radius"]:
                dict_user[key]["value"] = self.dict_user_plot[key]["value"]
                    #set default values for null values
            if not dict_user["type"]["value"]:
                dict_user["type"]["value"] = "Rectangle"
            if not dict_user["width"]["value"]:
                dict_user["width"]["value"] = 0
                dict_user["length"]["value"] = 0
                dict_user["radius"]["value"] = 0

        #in any case ajust dict_user trees and plots
        if table == 'plots':
            dict_user['radius']["value"] = dict_user['width']["value"]
            self.dict_user_plot = copy.deepcopy(dict_user)
        elif table == 'trees':
            #restore history index to 0
            dict_user["history"]["value"] = 0
            dict_user["history"]["items"] = list_db_tree_history[1:]
            self.dict_user_tree = copy.deepcopy(dict_user)


    def get_dict_update(self, table):
    #return a update dictionnary to save in the database (={"id":id,  "table":table, + fields with value})
        dict_user = {}
        if table == "trees":
            dict_user = self.dict_user_tree
            field_id = "id_tree"
        elif table == "plots" :
            dict_user = self.dict_user_plot
            field_id = "id_plot"
        id = dict_user[field_id]["value"]
        #detect for new record
        isNew = not isinstance(id, int)
        if isNew:
            id = None
        dict_update ={"id":id, "table":table}
        #create the tab_update according to the field_def properties (visible, enabled)
        for field_name, field_def in dict_user.items():
            if not field_def.get ("enabled", True):
                continue
            #must be visible and New or Changed
            if field_def.get ("visible", True) and (isNew or field_def.get ("changed", False)) :
                value = field_def["value"]
                if field_name == "radius":
                    field_name = "width"
                dict_update[field_name] = value
        #if fields to update
        if len(dict_update) > 2:
            return dict_update
        return {}

    def update_data_ui (self, dict_update):
    #update the UI according to the dict_update
        #local function
        def update_tableview_data( model, column_id):
        #Internal function to update model of tableview (trees or plot) according to dict_update
            dict_headers = {model.headerData(i, Qt.Horizontal):i for i in range(model.columnCount()) if dict_update.get(model.headerData(i, Qt.Horizontal), False)}
            if not dict_headers:
                return
            #loop on the model to search for tab_ids and columns to update
            for row in range(model.rowCount()):
                index = model.index(row, column_id)
                if model.data(index, role = Qt.UserRole) in tab_ids:
                    for key, column in dict_headers.items():
                        value = self.tableview_formated_value(dict_update[key])
                        rowindex = index.siblingAtColumn(column)
                        model.setData(rowindex, value, role=Qt.DisplayRole)
    ######begining of the main function
        #get the id(s) set to a list of integer
        tab_ids = dict_update["id"]
        if not isinstance(tab_ids, list):
            tab_ids = [tab_ids]
        tab_ids = list(map(int, tab_ids))
        #set the model
        if dict_update["table"] == "plots":
            model = self.ui.tableView_plots.model()
            #model_edit = self.ui.tableView_plot.model()
        else:
            model = self.ui.tableView_trees.model()
            #model_edit = self.ui.tableView_tree.model()
        #refresh tableview plots and trees (both if plots because of commons plot name)
        
        update_tableview_data (model, 0)
        if dict_update["table"] == "plots":
            update_tableview_data(self.ui.tableView_trees.model(), 1)
        # print ("before update_tableview_data")
        #search for update in row headers of tree and plot edition lists
        # num_rows = model_edit.rowCount()
        # id = tab_ids[0]
        # dict_user = {model_edit.index(i, 0).data().lower():i for i in range(num_rows) if dict_update.get(model_edit.index(i, 0).data().lower(), False)}
        # if id and dict_user:
        #     if model_edit.index(0, 1).data() == id:
        #         for key, row in dict_user.items():
        #             value = self.tableview_formated_value(dict_update[key])
        #             model_edit.item(row, 1).setData(value, role = Qt.DisplayRole)
        # print ("after update_tableview_data")
    #if collection/locality in dict_update, update the list of collections and refresh plots
        if dict_update.get(self.current_collection, False):
            self.load_collections(dict_update[self.current_collection])
            self.load_plots(id)
            self.create_dict_user(False)
    #in any case update/refresh the tableview_resolution if taxaname updated
        if dict_update.get("taxaname", False):
            self.load_taxa()
            self.tableview_resolution_selectedItem(dict_update["taxaname"])
                                
    def save_dict_update(self, dict_update):
    #create the sql statement related to dict_update (dictionnary of update composed of id, table + fields and values)
        #define field_id (id_tree or id_plot)
        field_id = 'id_plot'
        table = dict_update["table"]
        if table == "trees":
            field_id = 'id_tree'
            dict_update["time_updated"] = QDateTime.currentDateTime()
        #manage id, as a list of string for SQL 
        ids = dict_update['id']
        if ids:
            if not isinstance(ids, list):
                ids = [ids]
            tab_ids = list(map(str, ids))
            ids = ",".join(tab_ids)
        #create tab for update, check for type coherence according to dict_db_ncpippn (dbase) definition        
        tab_update = []
        sql_column = []
        sql_value = []
        for key, value in dict_update.items():
            #transform value in sql string
            value = get_typed_value(key.lower(), value, True)
            if not value:
                continue
            tab_update.append(key + "=" + str(value))
            #add to insert if not NULL
            if value != 'NULL':
                sql_column.append(key)
                sql_value.append(str(value))
        #execute INSERT
        if sql_column and not ids: #new, execute Insert
            sql_query = f"INSERT INTO {DBASE_SCHEMA}.{table}"
            sql_query += f"({', '.join(sql_column)}) VALUES ({', '.join(sql_value)})"
            sql_query += f"\nRETURNING {field_id}"
        else: #or execute UPDATE
            sql_query = f"UPDATE {DBASE_SCHEMA}.{table}"
            sql_query += "\nSET " + ", ".join (tab_update)
            sql_query += f"\nWHERE {field_id} IN ({str(ids)})"
            sql_query += f"\nRETURNING {field_id}"
        #return if no sql_query
        if len(sql_query) == 0:
            return False
        
        #execute query (return id_plot/id_tree for insert/update)
        result = database_execute_query(sql_query)

        #Refresh UI if refresh is enabled (by default)
        if result and dict_update.get("refresh", True):
            #restore dict_db from database (trees or plots)
            self.set_dict_dbase(result, table)
            dict_update["id"] = result
            if table == "trees" and not ids: #a new tree was created (result by RETURNING id_tree)
                self.load_trees(id_tree = result)
            self.update_data_ui (dict_update)
            self.show_dict_user()
            
            
        #in any case (refresh or not) return True if result
        if result:
            return True
        else:
            return False
        


    def tableview_formated_value(self, value):
    #return the value formatted to be display in a tableview (plots, trees, plot, tree)
        if isinstance(value, QDateTime):
            value = value.toString("yyyy/MM/dd")
        else:
            value = get_str_value(value)
        return value

    def tableview_trees_filter(self, item):
        #create a filter on table_view_trees from an input itel
        taxa =""
        if item:
            taxa = item.data()
        self.ui.tableView_trees.model().setFilterFixedString(taxa)

    def tableview_trees_add_item(self, model, id_tree, id_plot, tab_tree):
    #add an item to the table_view_trees from a list tab_tree
        tab_items = []
        for item in tab_tree:
            item = self.tableview_formated_value(item)
            item = QtGui.QStandardItem(item)
            tab_items.append(item)
        tab_items[0].setData(id_tree, role=Qt.UserRole)
        tab_items[1].setData(id_plot, role=Qt.UserRole)
        model.appendRow(tab_items)
        return tab_items[0]
            
    def tableview_trees_del_items(self):
    #delete selected trees from the tableView_trees.model()
        selection_model = self.ui.tableView_trees.selectionModel()
        selection_model.selectionChanged.disconnect(self.create_dict_user)
        selected_indexes = self.ui.tableView_trees.selectionModel().selectedRows()
        model = self.ui.tableView_trees.model()
        rows = [item.row() for item in selected_indexes]
        # reverse the list to avoid messing up the indices
        if rows:
            rows.sort(reverse=True)
            for row in rows:
                model.removeRow(row)            
            index = self.ui.tableView_trees.currentIndex()
            self.ui.tableView_trees.selectionModel().select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            self.create_dict_user()
            self.load_taxa()
        selection_model.selectionChanged.connect(self.create_dict_user)
    
    def tableView_plots_del_items(self):
    #delete selected plot from the tableView_plots.model()
        selection_model = self.ui.tableView_plots.selectionModel()
        selection_model.selectionChanged.disconnect(self.load_trees_taxa)
        selected_indexes = self.ui.tableView_plots.selectionModel().selectedRows()
        model = self.ui.tableView_plots.model()
        rows = [item.row() for item in selected_indexes]
        # reverse the list to avoid messing up the indices
        if rows:
            rows.sort(reverse=True)
            for row in rows:
                model.removeRow(row)            
            index = self.ui.tableView_plots.currentIndex()
            self.ui.tableView_plots.selectionModel().select(index, QItemSelectionModel.Select | QItemSelectionModel.Rows)
            self.load_trees_taxa()
        selection_model.selectionChanged.connect(self.load_trees_taxa)



    # def model_changed(self, model):
    # #check if model has changed (stocked in UserRole (True/False))
    #     try:
    #         ischanged = model.itemFromIndex(model.index(0,0)).data(Qt.UserRole)
    #     except:
    #         ischanged = False
    #     if ischanged:
    #         return ischanged
    #     else:
    #         return False


    


    def tableview_plots_dropEvent(self, event):
    #manage drop event on treeView_collections
        super().dropEvent(event)
        #event.ignore()
        target_index = self.ui.tableView_plots.indexAt(event.pos()).siblingAtColumn(0)
        #row = self.ui.tableView_trees.currentIndex() #target_index.row()
        #self.ui.tableView_plots.viewport().update()
        if event.source() == self.ui.tableView_trees:
            # selection = self.ui.tableView_plots.selectionModel()
            # selection.selectionChanged.disconnect()
            if target_index.isValid() : #and target_index.parent().isValid():
                selected_indexes = self.ui.tableView_trees.selectionModel().selectedRows()
                ids = [str(index.data(role=Qt.UserRole)) for index in selected_indexes]
                new_idplot = str(target_index.data(Qt.UserRole))
                msg = f"Are you sure to move the selected occurrence(s)\n to the plot < {target_index.data()} >?"
                if QMessageBox.question(None, "Move Occurrences", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    dict_update = {"id":ids, "table": "trees", "id_plot":new_idplot, "refresh":False}
                    #self.save_dict_update(dict_update)
                    if self.save_dict_update(dict_update):
                        self.tableview_trees_del_items()
                        #self.load_taxa()
        event.ignore()
        # QTest.mouseClick(self.ui.tableView_plots.viewport(), Qt.RightButton, Qt.NoModifier, QPoint(-100, -100))
        # return
        ###########################
        #simulate a click at the top-left corner of the viewport to hide DropIndicator (not a normal situation, it's just the way I found)
        #  Temporarily disable selections
        self.ui.tableView_plots.setSelectionMode(QAbstractItemView.NoSelection)
        pos = QPoint(-1, -1)
        mouse_event_press = QtGui.QMouseEvent(QEvent.MouseButtonPress, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        mouse_event_release = QtGui.QMouseEvent(QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self.ui.tableView_plots.viewport(), mouse_event_press)
        QApplication.sendEvent(self.ui.tableView_plots.viewport(), mouse_event_release)
        # Re-enable selections
        self.ui.tableView_plots.setSelectionMode(QAbstractItemView.ExtendedSelection)  # Restore the previous selection mode
        # Update the viewport to hide the drop indicator
        self.ui.tableView_plots.viewport().update()

    def tableview_resolution_selectedItem(self, taxa_search):
    #set the taxa_search in the tblView_resolution        
        model = self.ui.tblView_resolution.model()
        if model is None: 
            return
        for row in range(model.rowCount()):
            if model.index(row, 0).data() == taxa_search:
                self.ui.tblView_resolution.setCurrentIndex(model.index(row, 0))

    def treeView_collections_dragEnterEvent(self, event):
    #allow drag on treeView_collections only for self.ui.tableView_plots
        if event.source() == self.ui.tableView_plots:
            event.accept()

    def treeView_collections_dropEvent(self, event):
    #manage drop event on treeView_collections
        super().dropEvent(event)
        target_index = self.ui.treeView_collections.indexAt(event.pos())
        if not target_index.parent().isValid():
            return
        #self.ui.treeView_collections.viewport().update()
        if event.source() == self.ui.tableView_plots:
            if target_index.isValid():
                selected_indexes = self.ui.tableView_plots.selectionModel().selectedRows()
                ids = [str(index.data(role=Qt.UserRole)) for index in selected_indexes]                
                itemText = str(target_index.data()) #.replace("'", "''")
                msg = f"Are you sure to move the selected plot(s)\n to the {self.current_collection} < {target_index.data()} >?"
                if QMessageBox.question(None, "Move Plot", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    dict_update = {"id":ids, "table": "plots", self.current_collection:itemText, "refresh": False}
                    self.save_dict_update(dict_update)
                    self.tableView_plots_del_items()
                    # event.ignore()
                    return
        #add a virtual click to unfreeze treeView_collections
        event.ignore()
        #QTest.mouseClick(self.ui.treeView_collections.viewport(), Qt.LeftButton, Qt.NoModifier, QPoint(-1, -1))
        

    def treeView_collections_updateItem(self, index):
    #update the text of a node (collection, locality or plot) in treeView_collections
        new_name = index.data(Qt.DisplayRole).strip("'")
        old_name = index.data(Qt.UserRole).strip("'")
        if new_name == old_name : 
            return
        #create name for postgressql query
        str_new_collection = new_name.replace("'", "''")
        str_old_collection = old_name.replace("'", "''")
        sql_query = f"""UPDATE {DBASE_SCHEMA_PLOTS} 
                        SET {self.current_collection} = '{str_new_collection}' 
                        WHERE {self.current_collection} = '{str_old_collection}'
                    """
        #save into the dbase
        if database_execute_query(sql_query):
            #id_plot = self.get_current_id_plot()
            self.load_collections(new_name)
            #self.load_plots(id_plot)
            self.dict_user_plot[self.current_collection]["value"] = new_name
            #self.set_dict_dbase(id_plot, 'plots')
            self.show_dict_user()

            #self.create_dict_user()
        else:
            #Database error, restore previous text
            index.setData(old_name, Qt.DisplayRole)

    def treeview_scoretaxa_dbleClicked(self, index):
        if not index.isValid(): 
            return
        new_taxaname = index.siblingAtColumn(0).data()
        tab_name = self.ui.tabWidget_tree.currentWidget().objectName()
    #set the new taxaname
        if tab_name == 'tab_tree':
            self.data_changed("taxaname", new_taxaname)
        elif tab_name == 'tab_taxa':
            index = self.ui.tblView_resolution.currentIndex()
            old_taxaname = index.siblingAtColumn(0).data()
            model = self.ui.tableView_trees.model()
            ids = []
            #create the list of id_tree for occurrences matching with old_taxaname
            for index in model.match(model.index(0, 0), Qt.DisplayRole, old_taxaname, -1, Qt.MatchExactly | Qt.MatchRecursive):
                ids.append(str(index.data(Qt.UserRole)))
            if len(ids) > 0:
                msg = (
                        f"This action will change taxaname '{old_taxaname}' to '{new_taxaname}'\n\n"
                        f"Are you sure to apply transformation for {len(ids)} occurrence(s)?"
                      )
                if QMessageBox.question(None, "Identification", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                    dict_update = {"id":ids, "table": "trees", "taxaname": new_taxaname}
                    self.save_dict_update (dict_update)



    def slider_history_seturrentIndex(self, index):
    #create the dict_user_tree according to the slider index (0 is current set)
        dict_db_tree["history"]["value"] = 0
        if index > 0:
            self.dict_user_tree = dict_db_tree["history"]["items"][index-1]
            dict_db_tree["history"]["value"] = index
        else:
            self.dict_user_tree = copy.deepcopy(dict_db_tree)
        self.show_dict_user()

    def button_import_trees_click(self):
    #import new trees from a csv file in the current plot
        id_plot = self.get_current_id_plot()
        if not id_plot:
            return
        
        dict_import = {}
        tab_column = []
        tab_index_text = []
        row = 0
        #create the dict_import from dict_user_tree with only editable columns
        for field_name, field_def in dict_db_tree.items():
            if not field_def.get("enabled", True) or not field_def.get("visible", True):
                continue
            dict_import[field_name] = copy.deepcopy(field_def)
            dict_import[field_name]["value"] = None
            tab_column.append(field_name)
            #create a tab_index, a list of index of columns to casted as text type in the next loop
            if dict_db_ncpippn[field_name]["type"] in ["text", "memo"]:
                tab_index_text.append(row)
            row += 1
        #add id_plot as last colum
        dict_import["locality"] = copy.deepcopy(dict_db_plot["locality"])
        dict_import["longitude"] = copy.deepcopy(dict_db_plot["longitude"])
        dict_import["latitude"] = copy.deepcopy(dict_db_plot["latitude"])
        tab_column.append("id_plot")


        #load the class and UI
        test = CSVImporter(dict_import)
        test.load()
        test.show_modal()
        if test.rows_imported > 0:
            self.load_plots()
        print (str(test.rows_imported) + " trees imported")


    def button_new_tree_click(self):
    #add a new tree, copy the current self.dict_user_plot to inherit some values
        #if is an history data, restore it
        index_tree = dict_db_tree["history"]["value"]
        if index_tree > 0:
            msg = "Are you sure to restore the history data as the current record ?"
            msg += "\n all recent data will be deleted"
            if QMessageBox.question(None, "Restore History", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                id = dict_db_tree["id_tree"]["value"]
                time_updated = self.dict_user_tree["time_updated"]["value"]
                #restore a historical record
                tab_update = []
                #create the update query for any enabled field of the current dict_user_tree (history)
                dict_update = {"id":id, "table": "trees"}
                for field_name, field_def in self.dict_user_tree.items():
                    if field_name in ['id_tree', 'history']:
                        continue
                    if dict_db_tree[field_name].get ("visible", True):
                        value = field_def["value"]
                        #set the value to the dict_db_tree
                        dict_db_tree[field_name]["value"] = value
                        dict_update[field_name] = value                        
                        value = get_typed_value(field_name, value, True)
                        tab_update.append(field_name + " = " + str(value))
                        
                if tab_update:
                    #disable trigger before restoring history data
                    sql_query = f"ALTER TABLE {DBASE_SCHEMA_TREES} DISABLE TRIGGER trigger_on_update;"
                    sql_query += f"\nUPDATE {DBASE_SCHEMA_TREES}"
                    #sql_query += "\nSET " + ", ".join (tab_update)
                    sql_query += f"\nSET {', '.join (tab_update)}"
                    sql_query += f"\nWHERE id_tree = {id};"
                    sql_query += f"\nALTER TABLE {DBASE_SCHEMA_TREES} ENABLE TRIGGER trigger_on_update;"
                    sql_query +=  (
                        f"\nDELETE FROM {DBASE_SCHEMA_TREES}_history"
                        f"\nWHERE id_tree = {id} AND time_updated > TIMESTAMP '{time_updated.toString(DBASE_DATETIME_FORMAT)}' - INTERVAL '0.1 second'"
                            )
                if not database_execute_query(sql_query) :
                    print ('Error on database update', sql_query)
                    return
                #ajust the tree history list of items, keep only oldest records than current one
                dict_db_tree["history"]["items"] = dict_db_tree["history"]["items"][index_tree:]
                dict_db_tree["history"]["value"] = 0
                #update ui for edited value
                self.update_data_ui(dict_update)
        else:
            #set a new dbase record for plot
            self.set_dict_dbase(None, 'trees')
        self.show_dict_user()

    # def set_new_dict_user_trees(self):
    # #set dict_user_trees to new with defaut values
    #     self.set_dict_dbase(None, 'trees')
        #set default values for NEW
        # self.dict_user_tree["dead"]["value"] = False
        # self.dict_user_tree["month"]["value"] = datetime.now().month        
        # self.dict_user_tree["year"]["value"] = datetime.now().year

    def button_new_plot_click(self):
        self.set_dict_dbase(None, 'plots')
        self.show_dict_user()

    def button_apply_tree_click(self):
    #apply changed to trees table
        #verifiy for a valid id_plot
        id_plot = None
        id_plot = self.get_current_id_plot()
        if not id_plot:
            return
        #select indexes of selected rows
        selected_indexes = self.ui.tableView_trees.selectionModel().selectedRows()
        #get the dict update
        dict_update = self.get_dict_update("trees")
        dict_update["id"] = [index.data(role=Qt.UserRole) for index in selected_indexes]
        #add id_plot for insert new
        dict_update["id_plot"] = id_plot
        #save the dict_update
        self.save_dict_update(dict_update)        

    def button_apply_plot_click(self):
    #apply changed to plots table
        #check for coherence in data
        dict_user = self.dict_user_plot
        _type = dict_user["type"]["value"]
        area = None
        msg = None
        #check for value
        try: #check for longitude, latitude (mandatory and in special range)
            long = float (dict_user["longitude"]["value"])
            lat = float (dict_user["latitude"]["value"])
            if long < -180 or long > 180:
                msg = "Error: longitude must be a numeric value between -180 and 180"
            if lat < -90 or lat > 90:
                msg = "Error: latitude must be a numeric value between -90 and 90"
        except:
            msg = "Error: longitude and latitude must have a non-NULL numeric value"

        #check for type
        if not _type:
            msg = "Error: Type must have a non-NULL value (Rectangle, Point or Circle)"
        elif _type == 'Rectangle':
            try:
                area = float (dict_user["width"]["value"]) *  float (dict_user["length"]["value"])
                if area <= 0:
                    msg = "Error: a plot must have a positive area (width x length > 0)"
            except:
                msg = "Error: width or length must have a non-NULL numeric value"
        elif _type == 'Circle':
            try:
                if (float (dict_user["radius"]["value"])  ** 2) <= 0:
                    msg = "Error: a circular plot must have a positive area (radius > 0)"        
            except:
                msg = "Error: radius must have a non-NULL numeric value"

        #return a msg and quit if errors
        if msg:
            QMessageBox.critical(None, "Database error", msg, QMessageBox.Ok)
            return
        
        #save self.dict_user_plot if no errors
        dict_update = self.get_dict_update("plots")
        self.save_dict_update(dict_update)

    def button_cancel_tree_click(self):
    #restore the database tree definition
        self.dict_user_tree = copy.deepcopy(dict_db_tree)
        self.show_dict_user()

    def button_cancel_plot_click(self):
    #restore the database plot definition
        self.dict_user_plot = copy.deepcopy(dict_db_plot)
        self.show_dict_user()
    
    def button_delete_tree_click (self):
    #delete selected trees and/or trees history from the database
        index_tree = dict_db_tree["history"]["value"]
        if index_tree > 0:
            msg = "Are you sure to delete the history data ?"
            if QMessageBox.question(None, "Delete History", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                id = self.dict_user_tree["id_tree"]["value"]
                time_updated = self.dict_user_tree["time_updated"]["value"]
                #select historical record with an interval to ensure capture of the exact time
                sql_query =  (
                    f"DELETE FROM {DBASE_SCHEMA_TREES}_history"
                    f"\nWHERE id_tree = {id} AND time_updated BETWEEN TIMESTAMP '{time_updated.toString(DBASE_DATETIME_FORMAT)}' - INTERVAL '0.1 second'"
                    f"\nAND TIMESTAMP '{time_updated.toString(DBASE_DATETIME_FORMAT)}' + INTERVAL '0.1 second'"
                        )
                if not database_execute_query(sql_query) :
                    print ('Error on database delete', sql_query)
                    return
                #ajust the tree history list of items, delete the current one
                del dict_db_tree["history"]["items"][index_tree-1]
                dict_db_tree["history"]["value"] = 0
                self.dict_user_tree = copy.deepcopy(dict_db_tree)
                self.show_dict_user()
        else:

            msg = "Are you sure to delete the selected occurrence(s) ?"
            msg += "\nThis will remove all history data"
            if QMessageBox.question(None, "Delete Occurrences", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
                selected_indexes = self.ui.tableView_trees.selectionModel().selectedRows()
                ids = [str(index.data(role=Qt.UserRole)) for index in selected_indexes]
                sql_query =  (
                    f"DELETE FROM {DBASE_SCHEMA_TREES}"
                    f"\nWHERE id_tree IN ({', '.join (ids)})"
                        )
        #if database successful
                if not database_execute_query(sql_query) :
                    print ('Error on database delete', sql_query)
                    return
                self.tableview_trees_del_items()

    def button_delete_plot_click (self):
    #delete selected plot from the database
        #ids = str(id)
        plot_name = self.dict_user_plot["plot"]["value"]
        msg = f"Are you sure to delete the plot < {plot_name} > ?"
        msg += "\nThis will also remove all occurrences related to this plot"
        if QMessageBox.question(None, "Delete Plot", msg, QMessageBox.Yes, QMessageBox.No) == QMessageBox.Yes:
            id = self.dict_user_plot["id_plot"]["value"]            
            sql_query =  (
                    f"DELETE FROM {DBASE_SCHEMA_PLOTS}\nWHERE id_plot = {id}"
                    )
            if not database_execute_query(sql_query) :
                print ('Error on database delete', sql_query) #for debugging
                return
 
            #update the model to reflect database update
            row = 0
            try:
                model = self.ui.tableView_plots.model()
                for row in range(model.rowCount()):
                    index = model.index(row, 0)
                    if model.data(index, role = Qt.UserRole) == id:
                        model.removeRow(row)
                        selected_index = model.index(max(0, row-1),0)
                        self.ui.tableView_plots.setCurrentIndex(selected_index)
                        break
            except:
                pass


    def load_collections(self, itemText = None):
        model = QtGui.QStandardItemModel()
        #if not self.dbopen: return
        if itemText == -1:
            return
        print ("load_collections", itemText)
    #load the collection from the selected column (collection or locality)
        self.current_collection = self.ui.comboBox_collections.currentText().lower() 
        self.statusLabel.setText('Select a ' + self.current_collection)
        #create the sql statement
        sql_query = f"SELECT collection, locality FROM {DBASE_SCHEMA_PLOTS} \nGROUP BY collection, locality"
        sql_query += f"\nORDER BY {self.current_collection}"
        query = QtSql.QSqlQuery(sql_query)
 

        ls_collection = []
        ls_localities = []
        _dict_collection = {}
        item_root = QtGui.QStandardItem("< Plots >")
        model.appendRow(item_root)
       
        while query.next():
            #get values from query
            root_node = str(query.value(self.current_collection))
            locality = str(query.value("locality"))
            collection = str(query.value("collection"))
            #manage unreferenced plot
            if query.isNull(self.current_collection):
                root_node = "< no " + self.current_collection + " >"
            else:
                root_node = str(query.value(self.current_collection))
            # manage a local dictionnary to conserve the root nodes
            if root_node not in _dict_collection:
                _dict_collection[collection] = []
                collectionItem = QtGui.QStandardItem()
                collectionItem.setData(root_node, Qt.DisplayRole)
                collectionItem.setData(root_node, Qt.UserRole)
                item_root.appendRow([collectionItem])
                _dict_collection[root_node] = collectionItem
            # create the list of collection/localities for edition
            if collection not in ls_collection:
                ls_collection.append(collection)
            if locality not in ls_localities:
                ls_localities.append(locality)
        
        #set the collections and localities lists in the dict_db_plot
        dict_db_plot["collection"]["items"] = sorted(ls_collection)
        dict_db_plot["locality"]["items"] = sorted(ls_localities)        
        #set the model
        self.ui.treeView_collections.setModel(model)
        
        #disconnect the slot (if connected) before selecting
        selection_model = self.ui.treeView_collections.selectionModel()
        if itemText in[0,1]:
            #connect slot before (load_plots will be fired)
            selection_model.selectionChanged.connect(self.load_plots)
            item = model.index(0, 0)
            self.ui.treeView_collections.setCurrentIndex(item)
            self.ui.treeView_collections.expand(item_root.index())
        elif itemText in _dict_collection:
            item = _dict_collection[itemText]
            #connect slot after (load_plots will not be fired)
            self.ui.treeView_collections.setCurrentIndex(item.index())
            selection_model.selectionChanged.connect(self.load_plots)
        #connect the slots for editing
        model.itemChanged.connect(self.treeView_collections_updateItem)

        
    def load_plots(self, id_plot = None):
        print ("load_plots", id_plot)
    #load the plots according to the selected treeView_collections item (collection or locality)
        model_plots = QtGui.QStandardItemModel()
        try:
            current_terms = self.ui.treeView_collections.currentIndex().data()
            current_terms = current_terms.replace("'", "''")
        except:
            current_terms = None
        if not current_terms:
            return
        
        additional_term = 'collection'
        if self.current_collection == 'collection':
            additional_term = "locality"
        ls_columns = ['plot', additional_term, 'type', 'longitude', 'latitude', 'altitude']
        model_plots.setHorizontalHeaderLabels(ls_columns)
        

        _plottype = ""
        _tmp = []
        _sqlwhere = ''
        #create the sql statement
        if self.ui.treeView_collections.currentIndex().parent().isValid():
            _tmp.append(f"{self.current_collection} = '{current_terms}'")
        if self.ui.comboBox_types.currentIndex() > 0:
            _plottype = self.ui.comboBox_types.currentText()
            _plottype = f"\nAND type = '{_plottype}'"
            _tmp.append(f"type = '{self.ui.comboBox_types.currentText()}'")
        if len(_tmp) > 0:
            _sqlwhere = " WHERE " + " AND ".join(_tmp)
        #add virtual name (plot_name) by coalescence when plot is NULL
        # sql_query = f"""SELECT id_plot, COALESCE (plot, LEFT(TYPE, 1) ||  LPAD(id_plot::text, 6, '0')) as plot, {', '.join(ls_columns[1:])} 
        #               FROM ncpippn.plots 
        #               WHERE {self.current_collection} = '{current_terms}'{_plottype}
        #               ORDER BY {self.current_collection}, plot
        #               """
        # sql_query = f"""SELECT id_plot, COALESCE (plot, LEFT(TYPE, 1) ||  LPAD(id_plot::text, 6, '0')) as plot, {', '.join(ls_columns[1:])} 
        #               FROM ncpippn.plots {_sqlwhere}
        #               ORDER BY plot
        #               """        
        sql_query = f"""SELECT id_plot, plot, {', '.join(ls_columns[1:])} 
                      FROM {DBASE_SCHEMA_PLOTS} {_sqlwhere}
                      ORDER BY plot
                      """        
        query = QtSql.QSqlQuery(sql_query)
        #add the plot to the model_plots
        selected_index = None
        while query.next():
            tab_items = []
            for column in ls_columns:
                item = query.value(column)
                #format value in str
                if query.isNull(column):
                    item = None
                elif isinstance(item, QDateTime):
                    item = item.toString(DBASE_DATETIME_FORMAT)
                else:
                    item = str(item)
                #add value to model
                item = QtGui.QStandardItem(item)
                tab_items.append(item)
            
            if tab_items:
                item_idplot = query.value("id_plot")
                #set the virtual PlotName
                tab_items[0].setData(query.value("plot"), role = Qt.DisplayRole)
                tab_items[0].setData(item_idplot, role = Qt.UserRole)
                model_plots.appendRow(tab_items)
                if item_idplot == id_plot:
                    selected_index = tab_items[0].index()
        
        self.ui.tableView_plots.setModel(model_plots)
        self.ui.tableView_plots.horizontalHeader().setSortIndicator(0, Qt.DescendingOrder)
        #resize to content except taxa column (= stretch)
        self.ui.tableView_plots.resizeColumnsToContents()
        header = self.ui.tableView_plots.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        #disconnect slot (if connected) before updated
        selection = self.ui.tableView_plots.selectionModel()
        #selection.selectionChanged.disconnect()
        if not selected_index:
            #select the first row and connect slot before updating selection
            selected_index = model_plots.index(0,0)
            selection.selectionChanged.connect(self.load_trees_taxa)
            self.ui.tableView_plots.setCurrentIndex(selected_index)
        else:
            #set the current selected_index and connect slot after updating (not load_trees fired)
            self.ui.tableView_plots.setCurrentIndex(selected_index)
            self.ui.tableView_plots.scrollTo(selected_index, QAbstractItemView.PositionAtCenter)
            selection.selectionChanged.connect(self.load_trees_taxa)
    
    def load_trees_taxa(self):
    #a special function for tableview_plots slot, set resolution_model to None to enforce load_taxa
        self.ui.tblView_resolution.setModel(None)
        self.load_trees()

    def get_trees_sql_where(self):
        try:
            selected_indexes = self.ui.tableView_plots.selectionModel().selectedRows()
        except:
            selected_indexes = None
        if selected_indexes is None :
            return
        #create the sql_where statement
        _tabtmp = []
        #add id_plot selection
        first_column_indexes = [index.sibling(index.row(), 0) for index in selected_indexes]
        selected_plots = ",".join([str(index.data(Qt.UserRole)) for index in first_column_indexes])
        
        _tabtmp.append(f"a.id_plot IN ({selected_plots})")
        #add others filters
        if self.ui.filter_button_dead.isChecked():
            _tabtmp.append("dead")
        if self.ui.filter_button_trait.isChecked():
            _tabtmp.append("COALESCE (bark_thickness, leaf_area, leaf_sla, leaf_ldmc, wood_density) IS NOT NULL")
        if self.ui.filter_button_fruit.isChecked():
            _tabtmp.append("fruit")
        if self.ui.filter_button_flower.isChecked():
            _tabtmp.append("flower")            
        if self.ui.filter_button_allometry.isChecked():
            _tabtmp.append("dbh IS NOT NULL AND height IS NOT NULL")                 
        #create the final sql statement (add where accordind to _tabtmp)
        if len (_tabtmp) > 0:
            #sql_select += f"\nWHERE {' AND '.join(_tabtmp)}"
            return f"WHERE {' AND '.join(_tabtmp)}"

    def load_trees(self, id_tree = None):
        #if not self.dbopen: return
    #load the main tableview_trees with trees and plot information
        print ("load_trees", id_tree)
        #clear the list and create a proxy model        
        model_trees = QtGui.QStandardItemModel() #NCPIPPN_tree_model() #
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model_trees)
        proxy_model.setFilterKeyColumn(0)

        #create the query according to the treeview selected item and filters
        try:
            selected_indexes = self.ui.tableView_plots.selectionModel().selectedRows()
        except:
            selected_indexes = None
        if selected_indexes is None :
            return


        #create the query
        ls_columns = ['taxaname', 'identifier', 'plot', 'year', 'time_updated', 'dead']
        sql_select = f"""SELECT id_tree, a.id_plot, {', '.join(ls_columns)} 
                    FROM {DBASE_SCHEMA_TREES} a
                    INNER JOIN {DBASE_SCHEMA_PLOTS} b ON a.id_plot = b.id_plot
                    {self.get_trees_sql_where()}
                    ORDER BY {ls_columns[0]}
            """
        # #create the sql_where statement
        # _tabtmp = []
        # #add id_plot selection
        # first_column_indexes = [index.sibling(index.row(), 0) for index in selected_indexes]
        # selected_plots = ",".join([str(index.data(Qt.UserRole)) for index in first_column_indexes])
        
        # _tabtmp.append(f"a.id_plot IN ({selected_plots})")
        # #add others filters
        # if self.ui.filter_button_dead.isChecked():
        #     _tabtmp.append("dead")
        # if self.ui.filter_button_trait.isChecked():
        #     _tabtmp.append("COALESCE (bark_thickness, leaf_area, leaf_sla, leaf_ldmc, wood_density) IS NOT NULL")
        # if self.ui.filter_button_fruit.isChecked():
        #     _tabtmp.append("fruit")
        # if self.ui.filter_button_flower.isChecked():
        #     _tabtmp.append("flower")            
        # if self.ui.filter_button_allometry.isChecked():
        #     _tabtmp.append("dbh IS NOT NULL AND height IS NOT NULL")                 
        # #create the final sql statement (add where accordind to _tabtmp)
        # if len (_tabtmp) > 0:
        #     sql_select += f"\nWHERE {' AND '.join(_tabtmp)}"
        # sql_select += f"\nORDER BY {ls_columns[0]}"

        #load the query and fill the model
        query = QtSql.QSqlQuery(sql_select)
        selected_index = None
        #data = []
        while query.next():
            # get value from query
            tab_tree = []
            for column in ls_columns:
                item = query.value(column)
                tab_tree.append(item)
            #append item to the model
            if tab_tree:
                item = self.tableview_trees_add_item (model_trees, query.value("id_tree"), query.value("id_plot"), tab_tree)
                
                if id_tree == query.value("id_tree"):
                    selected_index = item.index()
        #set the model to the list view and connect slots
        # nb_plots = self.ui.tableView_plots.model().rowCount()
        # nb_plot_selected = len(self.ui.tableView_plots.selectionModel().selectedRows())
        # self.statusLabel.setText(str(nb_plots) +" (" + str(nb_plot_selected) + ") plot(s) - "+ str(rows) + " tree(s)")
        #model_trees.header_labels = ls_columns
        #model_trees.resetdata(data)
        self.ui.tableView_trees.setModel(proxy_model)
        
        model_trees.setHorizontalHeaderLabels(ls_columns)
        #self.ui.tableView_trees.setModel(proxy_model)
        selection_model = self.ui.tableView_trees.selectionModel()
        selection_model.selectionChanged.connect(self.create_dict_user)
        
        #resize to content except taxa column (= stretch)
        self.ui.tableView_trees.horizontalHeader().setSortIndicator(0, Qt.DescendingOrder)
        self.ui.tableView_trees.resizeColumnsToContents()
        header = self.ui.tableView_trees.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        
        #load the taxa if model is Null
        if not self.ui.tblView_resolution.model():
            self.load_taxa()        
        #select the first row (and trigger the function create_dict_user()), if empty force create_dict_user
        if selected_index:
            self.ui.tableView_trees.setCurrentIndex(selected_index)
        elif model_trees.rowCount() > 0:
            self.ui.tableView_trees.setCurrentIndex(proxy_model.index(0, 0))
        else: #no trees, force create_dict_user() to set new tree
            self.create_dict_user()


    def load_taxa(self):
        print ("load_taxa")
        #get the list of unique taxa in the tableView_trees
        model_trees = self.ui.tableView_trees.model()
        unique_taxa = set()
        for row in range(model_trees.rowCount()):
            taxaname = model_trees.index(row, 0).data()
            if taxaname :
                unique_taxa.add(taxaname)
        #create a PN_taxa_resolution_model from the list of unique_taxa
        self.ui.tblView_resolution.setModel(PN_taxa_resolution_model())
        #create sql statement from unique_taxa
        items_sql = ', '.join([f"'{item}'" for item in unique_taxa])
        sql_query = f"SELECT * FROM {DBASE_SCHEMA_TAXONOMY}.pn_taxa_searchnames(array[{items_sql}]) WHERE original_name IS NOT NULL ORDER BY original_name"
        data = []
        query = QtSql.QSqlQuery (sql_query)
        #add item as a PNsynonym class
        while query.next():
            newRow = PNSynonym(
                            query.value("original_name"), 
                            query.value("taxonref"),
                            query.value("id_taxonref") 
                            )
            data.append(newRow)
        if len(data) > 0:
            #reset the model and repaint the tblView_resolution
            self.ui.tblView_resolution.hideColumn(1)
            self.ui.tblView_resolution.resizeColumnsToContents()
            header = self.ui.tblView_resolution.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            selection = self.ui.tblView_resolution.selectionModel()
            selection.selectionChanged.connect(self.load_taxa_search)
            self.ui.tblView_resolution.model().resetdata(data)
            self.ui.tblView_resolution.doubleClicked.connect(self.tableview_trees_filter)
            #proxyModel.setFilterRegExp(f'.*zy.*|.*ch.*')
            #self.ui.tblView_resolution.repaint()


        
    # def load_tree_history (self):
    # #load history data related to the id_tree
    #     id_tree = dict_db_tree["id_tree"]["value"]
    #     if not id_tree : 
    #         return
    #     #purge historical items from dict_dbtree
    #     dict_db_tree["history"]["items"] = []
    #     dict_db_tree["history"]["value"] = 0
    #     # create and execute query
    #     sql_query = f"SELECT * FROM ncpippn.trees_history WHERE id_tree = {id_tree} ORDER BY time_updated DESC"
    #     query = QtSql.QSqlQuery(sql_query)
    #     list_db_tree_history = []
    #     while query.next():
    #         _tmp = copy.deepcopy(dict_db_tree)
    #     #set the data to two db dictionnaries
    #         for dbcolumn in _tmp.keys():
    #             value = None
    #             try:
    #                 if query.record().indexOf(dbcolumn) != -1:
    #                     if not query.isNull(dbcolumn):
    #                         value = query.value(dbcolumn)
    #                     _tmp[dbcolumn]["value"] = value                 
    #             except:
    #                 pass
    #         list_db_tree_history.append(_tmp)     
    #     #load the tree history
    #     dict_db_tree["history"]["items"] = list_db_tree_history
    #     dict_db_tree["history"]["value"] = 0
    #     return
    
    def load_taxa_search(self, item = None):
        self.tableview_trees_filter(None)
    #manage what happens when clicking on a tblView_resolution item
        if not isinstance(item, str):
        #if signal is not a text value, get the taxonref from the item index
        #and set to the lineEdit_search_taxa (triggering a new call throught text value)
            if item.indexes():
                self.ui.lineEdit_search_taxa.setText(item.indexes()[0].data())
            return
        #"main" function to search for taxa resolution
        search_txt = self.ui.lineEdit_search_taxa.text()
        _score = 0.4
        #exlude search according to number of characters
        if len(search_txt) < 4:
            return
        if len(search_txt) < 8:
            _score = 0.2
        #create sql query
        sql_query = f"""
            SELECT 
                a.taxonref, a.score, a.id_taxonref, c.original_name AS synonym
            FROM 
                {DBASE_SCHEMA_TAXONOMY}.pn_taxa_searchname('{search_txt}', {_score}::numeric) a 
            INNER JOIN 
                {DBASE_SCHEMA_TAXONOMY}.taxa_keynames2 c 
            ON 
                a.id_taxonref = c.id_taxonref
            ORDER 
                BY score DESC, synonym ASC
        """
        # sql_query = sql_query.replace('_searchterm', search_txt)
        # sql_query = sql_query.replace('_score', str(_score))

        #print (sql_query)
        #fill model with query result
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        query = QtSql.QSqlQuery (sql_query)
        dict_nodes = {}
        tab_header = ['taxonref', 'score']
        while query.next():
            id_taxonref = query.value('id_taxonref')
            if id_taxonref in dict_nodes:
                ref_item = dict_nodes[id_taxonref]
            else:
                #create the node if not already existed
                ref_item = [QtGui.QStandardItem(str(query.value(x))) for x in tab_header]
                ref_item[0].setData(id_taxonref, Qt.UserRole)
                ref_item[1].setTextAlignment(Qt.AlignCenter)
                model.appendRow(ref_item)
                dict_nodes[id_taxonref] = ref_item
                #set score in red if below 50
                if query.value('score') < 50:
                    _color =  QtGui.QColor(255, 0, 0)
                    ref_item[1].setData(QtGui.QBrush(_color), Qt.ForegroundRole)
            if query.value('synonym'):
                ref_item[0].appendRow ([QtGui.QStandardItem(query.value('synonym'))])
        #model.setHorizontalHeaderLabels(tab_header)
        
        self.ui.treeview_scoretaxa.setModel(model)
        self.ui.treeview_scoretaxa.setHeaderHidden(True)
        self.ui.treeview_scoretaxa.resizeColumnToContents(1)
        self.ui.treeview_scoretaxa.setExpanded(model.index(0, 0), True)
        self.ui.treeview_scoretaxa.header().setStretchLastSection(False)
        self.ui.treeview_scoretaxa.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.ui.treeview_scoretaxa.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        
        selection = self.ui.treeview_scoretaxa.selectionModel()
        selection.selectionChanged.connect(self.set_buttons_taxa_enabled)



    def create_dict_user(self, refresh = True):
    #function to fill the properties pannel (plot and tree) from the selected item
        #call by slot on tableview_trees selectionChanged
        index = self.ui.tableView_trees.currentIndex()
        id_tree = index.siblingAtColumn(0).data(Qt.UserRole)
        # model = self.ui.tableView_trees.model()
        # source_index = model.mapToSource(index)
        # id_tree = model.sourceModel().get_idtree (source_index.row())

        id_plot = self.get_current_id_plot()
        if id_plot != dict_db_plot["id_plot"]["value"]:
            self.set_dict_dbase(id_plot, 'plots')
        #if no id_trees set a new trees
        if id_tree != dict_db_tree["id_tree"]["value"]:
            self.set_dict_dbase(id_tree, 'trees')
            self.tableview_resolution_selectedItem(dict_db_tree["taxaname"]["value"])
        if refresh:
            self.show_dict_user()


    def show_dict_user(self):
        print ("show_dict_user")
    #fill the the two tableViews (tree and plot) with the two dict_user (dict_user_plot and dict_user_tree)
        def fill_model(dict):
            is_changed = False
            model = QtGui.QStandardItemModel()
            for field_name, field_def in dict.items():
                visible = field_def.get("visible", True)
                if not visible:
                    continue
                item = QtGui.QStandardItem()
                item1 = QtGui.QStandardItem()            
                field_name = str(field_name).capitalize()
                value = field_def["value"]
                type = field_def.get("type", 'text')
                item.setData(field_name, QtCore.Qt.DisplayRole)
                if type == 'date'and value:
                    value = value.toString("d MMMM yyyy")
                if type == 'boolean':
                    #add checkbox item for boolean
                    item1.setCheckable(True)
                    if value:
                        item1.setCheckState(Qt.Checked)
                    #manage enabled for checkbox
                    _enabled = field_def.get("enabled", True) and is_editable and is_alive
                    if field_name.lower() == "dead" and is_editable and not is_alive:
                        _enabled = True
                    item1.setEnabled(_enabled)
                elif field_def.get("items", None): 
                    if isinstance(value, int):
                        value = field_def["items"][value]
                    item1.setData(value, QtCore.Qt.DisplayRole)
                else:
                    item1.setData(value, QtCore.Qt.DisplayRole)
                if field_def.get("changed", False):
                    font = QtGui.QFont()
                    font.setBold(True) 
                    item.setFont(font)
                    is_changed = True

                model.appendRow([item, item1])
                model.itemFromIndex(model.index(0,0)).setData(is_changed, Qt.UserRole)
                model.itemChanged.connect(self.checkbox_changed)
                #set the changed flag as a data role on the cell (0,0)
            return model, is_changed
        
    #update the dict_user according to type (calculate area and manage visibility of rows)
    #check for plot
        is_alive = True
        is_editable = True
        area = None
        nb_plots = self.ui.tableView_plots.model().rowCount()
        nb_trees = self.ui.tableView_trees.model().rowCount()
        nb_plot_selected = len(self.ui.tableView_plots.selectionModel().selectedRows())
        nb_trees_selected = len(self.ui.tableView_trees.selectionModel().selectedRows())
        nb_taxa =  self.ui.tblView_resolution.model().rowCount()
        msg = f"{nb_plots} Plot(s), {nb_plot_selected} selected - {nb_trees} Tree(s)"
        if nb_trees > 0:
            msg += f", {nb_trees_selected} selected, {nb_taxa} taxon(s)"
        self.statusLabel.setText(msg)

        _type = self.dict_user_plot["type"]["value"]
        if _type:
            _type = _type.lower()
        _width = self.dict_user_plot["width"]["value"]
        _radius = self.dict_user_plot["radius"]["value"]
        _length = self.dict_user_plot["length"]["value"]
        is_rectangle = (_type == 'rectangle')
        is_circle = (_type == 'circle')
        #check for width and length to define type, area and width name
        if is_rectangle:
            try:
                area = _width * _length
            except:
                area = '<< error >>'
        elif is_circle:
            try:
                area = 3.141592654 * (_radius ** 2)
            except:
               area = '<< error >>'
        self.dict_user_plot["area"]["value"] = area        
        #set the visibility of some rows according to type
        self.dict_user_plot["width"]["visible"] = is_rectangle
        self.dict_user_plot["length"]["visible"] = is_rectangle
        self.dict_user_plot["radius"]["visible"] = is_circle
        self.dict_user_plot["area"]["visible"] = (is_rectangle or is_circle)
        self.dict_user_plot["plot"]["visible"] = (is_rectangle or is_circle)
        #set the enabled of edit buttons for plot
        id_plot = dict_db_plot["id_plot"]["value"]
        is_plot = isinstance(id_plot, int)
        self.button_delete_plot.setEnabled(is_plot)
        self.ui.button_import_trees.setEnabled(is_plot)
        #fill the model with dict_user_plot values
        model_plot,is_plot_changed = fill_model(self.dict_user_plot)
        #get the flag for plot changed (data.index(0,0), QT.userrole)
        #is_plot_changed = self.model_changed (model_plot)
        self.button_apply_plot.setEnabled(is_plot_changed)
        self.button_cancel_plot.setEnabled(is_plot_changed)
        #set the model and resize columns
        self.ui.tableView_plot.setModel(model_plot)
        self.ui.tableView_plot.resizeColumnsToContents()
        header = self.ui.tableView_plot.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

    # for trees, manage visibility of rows according to _type
        self.dict_user_tree["x"]["visible"] = is_rectangle
        self.dict_user_tree["y"]["visible"] = is_rectangle
        is_current = dict_db_tree["history"]["value"] == 0
        is_alive = not dict_db_tree["dead"]["value"]
        is_editable = (is_plot and is_current)
        #check for new tree (if not plot) and multiple selection
        if not is_plot:
        #set to new tree if no plot
            self.set_dict_dbase(None, 'trees')
        elif nb_trees_selected > 1:
            #Set visibility of rows if multiple selection on self.ui.tableView_trees
            for key in self.dict_user_tree:
                if key.lower() not in ['id_tree','taxaname', 'month', 'year', 'strata', 'flower', 'fruit']:
                    self.dict_user_tree[key]["visible"] = False
        #fill the model
        model_tree, is_tree_changed = fill_model(self.dict_user_tree)
        #is_tree_changed = self.model_changed (model_tree)

        #set the edit triggers
        if is_editable and is_alive:
            self.ui.tableView_tree.setEditTriggers(QTableView.CurrentChanged | QTableView.SelectedClicked)
        elif not is_alive: #mode read only if dead
            self.ui.tableView_tree.setEditTriggers(QTableView.NoEditTriggers)
        else: #mode read only if history or not id_plot
            self.ui.tableView_tree.setEditTriggers(QTableView.NoEditTriggers)
            is_tree_changed = False
        
        #set the enabled of edit buttons for tree            
        id_tree = self.dict_user_tree["id_tree"]["value"]
        is_tree = isinstance(id_tree, int)
        self.button_delete_tree.setEnabled(is_tree)
        self.button_apply_tree.setEnabled(is_tree_changed) # and is_plot)
        self.button_cancel_tree.setEnabled(is_tree_changed)
        self.button_new_tree.setEnabled(is_plot)
        self.ui.frame_history_slider.setVisible(False)
        # set model to tableView_tree
        self.ui.tableView_tree.setModel(model_tree)
        
        # resize columns
        self.ui.tableView_tree.resizeColumnsToContents()
        header = self.ui.tableView_tree.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)         

        #set the default height and  default height (4 rows visible) for memo field
        default_height = self.ui.tableView_tree.verticalHeader().defaultSectionSize()
        for row in range(model_tree.rowCount()):
            item = model_tree.item(row, 0)
            self.ui.tableView_tree.setRowHeight(row, default_height)
            if dict_db_tree[item.text().lower()]["type"] == 'memo':
                self.ui.tableView_tree.verticalHeader().resizeSection(row, 4*default_height)
        
        #set the history slider
        if not is_tree:
             return        
        try:
            self.ui.slider_history.valueChanged.disconnect(self.slider_history_seturrentIndex)
            list_db_tree_history = dict_db_tree["history"]["items"]
            self.ui.history_year_max.setText(str(dict_db_tree["time_updated"]["value"].date().year()))
            self.ui.history_year_min.setText(str(list_db_tree_history[-1]["time_updated"]["value"].date().year()))
            self.ui.slider_history.setMaximum(len (list_db_tree_history)) 
            self.ui.slider_history.setValue(dict_db_tree["history"]["value"])
            self.ui.frame_history_slider.setVisible(True)
        except:
            self.ui.frame_history_slider.setVisible(False)
        self.ui.slider_history.valueChanged.connect(self.slider_history_seturrentIndex)
        #switch the text of the new button
        if is_current:
            self.button_new_tree.setText("New")
        else:
            self.button_new_tree.setText("Restore")

    def get_current_id_plot(self):
    #get the current id_plot, hello world first from a tree if selected and from the treeView_collections (selected item or first item) if no tree selected 
        try:
            index = self.ui.tableView_trees.currentIndex()
            id_plot = index.siblingAtColumn(1).data(Qt.UserRole)
            #id_plot = self.ui.tableView_trees.model().sourceModel().get_idplot(index.row())
            if not id_plot: #search for plot selection in tableview_plots
                index = self.ui.tableView_plots.currentIndex()
                id_plot = index.siblingAtColumn(0).data(role=Qt.UserRole)
            return id_plot
        except:
            return
     
#manage changes in data coming from signals (checkbox and delegate)
    def checkbox_changed(self, itemcheckable):
    #only managed checkbox
        model= self.ui.tableView_tree.model()
        header = model.indexFromItem(itemcheckable).siblingAtColumn(0).data().lower()
        if dict_db_ncpippn[header]["type"] != 'boolean':
            return
        value = None
        if itemcheckable.checkState() == 2:
            value = True
        self.data_changed (header, value)

    def text_changed(self, header, new_value):
    #signal when a text is currently changed
        if header != "taxaname":
            return
        self.ui.lineEdit_search_taxa.setText(new_value)

    def data_changed(self, header, new_value):
    #manage all data update througth delegate
        dict_user = self.dict_user_plot | self.dict_user_tree
        dict_header = dict_user[header]
        dict_header["value"] = new_value
        dict_header["changed"] = (new_value !=  dict_db_ncpippn[header]["value"])      
        self.show_dict_user()

    def set_buttons_taxa_enabled(self):
    #set the buttons Replace/synonym to enabled according to the selected taxa in resolution and treeview_score_taxa
        selecteditem = self.ui.tblView_resolution.currentIndex()
        selectedtaxa = self.ui.treeview_scoretaxa.currentIndex()
        is_enabled = selecteditem.isValid() and selectedtaxa.isValid()
        self.ui.button_replace_taxa.setEnabled (is_enabled)
        self.ui.button_add_synonym.setEnabled (is_enabled)

        #check for other constraints
        if is_enabled:
            selecteditem = self.ui.tblView_resolution.model().data(selecteditem, Qt.UserRole)
            if selectedtaxa.parent().isValid():
                selectedtaxa = selectedtaxa.parent()
            is_resolved = selecteditem.resolved
            is_different = (selecteditem.id_taxonref != selectedtaxa.data(Qt.UserRole))
       
        self.ui.button_replace_taxa.setEnabled (is_enabled and is_different)
        self.ui.button_add_synonym.setEnabled (is_enabled and not is_resolved)

    def replace_taxanames(self):
        index = self.ui.treeview_scoretaxa.currentIndex()
        self.treeview_scoretaxa_dbleClicked(index)

    def add_synonym(self):
        #function calls by button signals
        def on_cancel_clicked():
            ui_syno.close()
        def on_ok_clicked():
            synonym_name = ui_syno.label_synonym_taxa.text()
            synonym_type = ui_syno.comboBox_synonym_type.currentText()
            str_idtaxonref = str(selectedtaxa.data(Qt.UserRole))
            sql_query = f"SELECT {DBASE_SCHEMA_TAXONOMY}.pn_taxa_edit_synonym ('{synonym_name}','{synonym_type}',{str_idtaxonref})"
            # sql_query = sql_query.replace('_newsynonym', synonym_name)
            # sql_query = sql_query.replace('_type', synonym_type)
            # sql_query = sql_query.replace('_idtaxonref', str_idtaxonref)
            ui_syno.close()
            if not database_execute_query(sql_query):
                print ("Error edit synonyms:", sql_query)
            self.load_taxa()
            
    #start of function defition
        index = self.ui.tblView_resolution.currentIndex()
        selecteditem = self.ui.tblView_resolution.model().data(index, Qt.UserRole)
        selectedtaxa = self.ui.treeview_scoretaxa.currentIndex()
        if not selecteditem:
            return
        if selecteditem.resolved:
            return
        if selectedtaxa.parent().isValid():
            selectedtaxa = selectedtaxa.parent()
        if not selectedtaxa.isValid():
            return   
        # load the GUI and connect signals
        ui_syno = uic.loadUi("pn_addsynonym2.ui")
        ui_syno.setWindowTitle(selectedtaxa.data())
        ui_syno.label_synonym_taxa.setText(selecteditem.synonym)
        ui_syno.buttonBox_synonym.accepted.connect(on_ok_clicked)
        ui_syno.buttonBox_synonym.rejected.connect(on_cancel_clicked)
        #adjust size and open dialog
        ui_syno.adjustSize()
        #ui_syno.setupUi(dialog)
        ui_syno.exec_()

    def close(self):
        self.ui.close()

    def show(self):
        self.ui.show()
        #self.window.exec_()

if __name__ == '__main__':
# connection to the database
    # db = QtSql.QSqlDatabase.addDatabase("QPSQL")
    # if not createConnection(db):
    #     sys.exit("error")
    app = QApplication(sys.argv)

    with open("Diffnes.qss", "r") as f:
        #with open("Photoxo.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)


    window = MainWindow()
    window.show()
    app.exec()

