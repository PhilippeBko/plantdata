from PyQt5 import uic, QtWidgets, QtGui, QtSql
from PyQt5.QtCore import Qt, pyqtSignal

#import commons
from commons import get_dict_from_species

#from taxa_model import PNTaxa
from api_thread import API_TAXREF, API_ENDEMIA, API_FLORICAL


class PNSynonym(object):
    def __init__(self, synonym, taxonref = None, idtaxonref = 0, idsynonym = 0, category = 'Orthographic'):
        self.synonym = synonym
        self.category = category
        self.taxon_ref = taxonref
        self.id_taxonref = idtaxonref
        self.id_synonym = idsynonym
        self.suggested_id_taxonref = 0
        self.suggested_name_taxon_ref = None
        self.keyname =''

    @property
    def idtaxonref(self):
        try:
            return int(self.id_taxonref)
        except:
            return 0

    @property
    def resolved(self):
        #return True if idtaxonref>0 
        return self.idtaxonref > 0  

    @property
    def idsynonym(self):
        try:
            return int(self.id_synonym)
        except:
            return 0

    @property
    def cleaned_name(self):
        if len(self.self.keyname) == 0:
            sql_query = "SELECT taxonomy.pn_taxa_keyname('__taxaname__') AS keyname"
            sql_query = sql_query.replace("__taxaname__", self.taxon_ref)
            query = QtSql.QSqlQuery (sql_query)
            if query.next():
                return query.value('keyname')
        else:
            return self.self.keyname


class PN_add_synonym (QtWidgets.QWidget):
    button_click = pyqtSignal(object, int)
    def __init__(self, myPNTaxa):

        super().__init__()
        self.window = uic.loadUi("pn_addsynonym.ui")
        self.myPNTaxa = myPNTaxa
        self.table_taxa = []
        self.data_rank = []
        self.updated = False

        #self.window.setWindowTitle("Add Taxa")          

        model = QtGui.QStandardItemModel()
        #model.setHorizontalHeaderLabels(['Rank','Taxon'])        
        model.setHorizontalHeaderLabels(['Taxa', 'Category'])          
       # model.itemChanged.connect(self.tblview_api_click)
        

        self.window.tblview_api.setModel(model)
        selection = self.window.tblview_api.selectionModel()
        selection.currentChanged.connect(self.tblview_api_before_clickitem)
        self.window.tblview_api.clicked.connect(self.tblview_api_click)

        self.window.tblview_api.setColumnWidth(0,250)
        self.window.tabWidget_main.currentChanged.connect(self.alter_category)
        self.Qbutton_OK = self.window.buttonBox
        self.Qbutton_OK.rejected.connect (self.close)
        #button = self.window.buttonBox.button(QDialogButtonBox.Apply)
        self.window.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
        #button.clicked.connect(self.apply)


    def close(self):
        self.window.close()
    def show(self):
        self.window.show()
        self.window.exec_()       


    def tblview_api_before_clickitem(self, current_index, previous_index):
        try:
            column2_index = self.window.tblview_api.model().itemFromIndex(previous_index).index()
            self.window.tblview_api.setIndexWidget(column2_index, None)
        except:
            pass

    def tblview_api_click(self):
            #tlview_identity_get_dict_properties(tlview_identity.model())
        if self.window.tblview_api.currentIndex().column() != 1:
            return
        # item = self.window.tblview_api.model().itemFromIndex(self.window.tblview_api.currentIndex())
        # if not item.isCheckable():
        #     return

        try:
            #field_name = self.window.tblview_api.currentIndex().siblingAtColumn(0).data()
            field_value = self.window.tblview_api.currentIndex().siblingAtColumn(1).data()
        except:
            return
        #try:
        column2_index = self.window.tblview_api.model().itemFromIndex(self.window.tblview_api.currentIndex()).index()

        combo_shortcut = QtWidgets.QComboBox()
        font = QtGui.QFont()
        font.setPointSize(10)
        combo_shortcut.setFont(font)
        combo_shortcut.setFrame(False)
        #combo_shortcut.setStyleSheet("QComboBox { color: white;background-color: rgb(46, 52, 54);gridline-color:yellow; border-radius: 5px;}") 
        style_sheet ="QComboBox QAbstractItemView {background-color: rgb(46, 52, 54)} "
        style_sheet +="QComboBox {selection-background-color:black; selection-color:yellow; color: rgb(239, 239, 239);background-color: rgb(46, 52, 54); border-radius: 3px}"
        style_sheet +="QComboBox::drop-down:button{background-color: rgb(46, 52, 54)} "
        combo_shortcut.setStyleSheet(style_sheet)
        #combo_shortcut.setStyleSheet("QComboBox { color: white;background-color: rgb(46, 52, 54)}")
        _properties =['Orthographic', 'Nomenclatural', 'Taxinomic', 'Vernacular']
        combo_shortcut.addItems(_properties)
        combo_shortcut.setCurrentText(field_value.title())
        combo_shortcut.currentIndexChanged.connect(self.tblview_api_combo_click)
        
        self.window.tblview_api.setIndexWidget(column2_index, combo_shortcut)

    def tblview_api_combo_click(self, index):
        if self.window.tblview_api.currentIndex().column() !=1: 
            return
        _properties =['Orthographic', 'Nomenclatural', 'Taxinomic', 'Vernacular']
        _value =_properties[index]
        item = self.window.tblview_api.model().itemFromIndex(self.window.tblview_api.currentIndex())
        item.setText(_value)

    def alter_category(self, index):
        #index = self.window.comboBox_searchAPI.currentIndex()
        if index == 0 : 
            #self.taxaLineEdit_setdata()
            return
        self.window.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
        #self.window.setCursor(Qt.WaitCursor)
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
        layout = self.window.tabWidget_main.currentWidget().layout()
        widget = None
        if layout is None:
            layout = QtWidgets.QGridLayout()
            self.window.tabWidget_main.currentWidget().setLayout(layout)
            layout.addWidget(self.window.tblview_api)
            widget = QtWidgets.QLabel()
            widget.setText('Check the taxa to add')
            layout.addWidget(widget)
        else:            
            layout.addWidget(self.window.tblview_api)
        index = self.window.tabWidget_main.currentIndex()
        #_apibase = index.text().lower()
        _apibase = self.window.tabWidget_main.tabText(index).lower()
        if _apibase == 'taxref':
            table_taxa = API_TAXREF(self.myPNTaxa).get_synonyms()
        elif _apibase == 'endemia':
            table_taxa = API_ENDEMIA(self.myPNTaxa).get_synonyms()
        # elif _apibase == 'powo':
        #     table_taxa = API_POWO(self.myPNTaxa).get_synonyms()
        elif  _apibase == 'florical':
            table_taxa = API_FLORICAL(self.myPNTaxa).get_synonyms()
            #restore original cursor
        self.window.tblview_api.model().setRowCount(0)
        self.window.tblview_api.repaint()

        while QtWidgets.QApplication.overrideCursor() is not None:
            QtWidgets.QApplication.restoreOverrideCursor()
        #self.window.setCursor(Qt.ArrowCursor)
        try:
            if len(table_taxa) == 0:
                return
        except:
            return

        #sort the list
        self.table_taxa = []
        sort_taxa = []
        for taxa in table_taxa:
            if taxa not in sort_taxa: #eliminate duplicate
                sort_taxa.append(taxa.strip())
                
        sort_taxa = sorted(sort_taxa)

        #add special fields and construct the query
        _taxaname=''
        _parser=''        
        try:
            for taxa in sort_taxa:
                _taxaname += _parser +"'" +taxa +"'"
                _parser=", "
        except:
            pass
        
         #check the taxaname into the taxa tables, and alters the id_taxonref
        sql_query = "SELECT COALESCE(id_taxonref,0) AS id_taxonref, original_name FROM taxonomy.pn_taxa_searchnames( array[_taxaname]) ORDER BY original_name"        
        sql_query = sql_query.replace('_taxaname', _taxaname)
        query = QtSql.QSqlQuery (sql_query)
        #set the id_taxonref for taxa already existing into the taxonomy tables
        model = self.window.tblview_api.model()
        model.setRowCount(0)
        model.setColumnCount(2)
        for taxa in sort_taxa:
            table_taxa = get_dict_from_species(taxa)
            table_taxa["id_taxonref"] = 0
            self.table_taxa.append(table_taxa)

        while query.next():
            taxa = query.value("original_name")
            item = QtGui.QStandardItem(taxa)
            item.setCheckable(query.value("id_taxonref")==0)
            self.window.tblview_api.model().appendRow([item, QtGui.QStandardItem("Taxinomic"), ])

        self.window.tblview_api.resizeColumnToContents(0)
        self.window.tblview_api.horizontalHeader().setStretchLastSection(True)
       # print (self.table_taxa)
        #self.draw_result()


    def draw_result(self):
        model = self.window.tblview_api.model()
        model.setRowCount(0)
        model.setColumnCount(4)
        #self.draw_list ()
        if model.rowCount() ==0:
            model.appendRow([QtGui.QStandardItem("No data   "), QtGui.QStandardItem("< Null Value >")],)
        # self.window.trView_childs.hideColumn(2)
        # self.window.trView_childs.hideColumn(3)
        # self.window.trView_childs.expandAll()
        # self.window.trView_childs.resizeColumnToContents(0)
        # self.window.trView_childs.resizeColumnToContents(1)
        # self.window.trView_childs.sortByColumn(1, Qt.AscendingOrder)










class PN_edit_synonym (QtWidgets.QWidget):
    button_click = pyqtSignal(object, int)
    def __init__(self, myPNSynonym):

        super().__init__()
        self.ui_addname = uic.loadUi("edit_name.ui")
        self.Qline_search = self.ui_addname.ref_search
        self.Qline_name = self.ui_addname.name_linedit
        self.Qline_ref = self.ui_addname.taxaLineEdit #self.ui_addname.ref_linedit
        self.Qcombobox = self.ui_addname.comboBox
        self.Qtreeview_search = self.ui_addname.tree_search
        self.frame_treeview = self.ui_addname.frame_treeview
        buttonbox = self.ui_addname.buttonBox
        #buttonbox.setEnabled(False)
        self.button_cancel = buttonbox.button(QtWidgets.QDialogButtonBox.Cancel)
        self.button_ok = buttonbox.button(QtWidgets.QDialogButtonBox.Ok)


        self.myPNSynonym = myPNSynonym

    def setting_ui(self):
        self.updated = False
        self.Qline_name.setReadOnly(False)
        self.Qline_name.setText('') 
        self.Qtreeview_search.setModel(QtGui.QStandardItemModel())
        self.ui_addname.setMaximumHeight(500)
        self.ui_addname.resize(500,500)
        self.ui_addname.tree_search.setVisible(True)
        self.Qcombobox.setCurrentText(str(self.myPNSynonym.category))
        self.Qline_name.setText(self.myPNSynonym.synonym)


        if not self.myPNSynonym.resolved:
            #setting the treeview model
            
            self.Qline_search.setText(self.myPNSynonym.synonym)
            self.Qline_ref.setText('')
            self.frame_treeview.setVisible(True)
            self.Qline_name.setReadOnly(True)
            self.search_for_text()
        else:
            #self.Qline_name.setText(self.myPNSynonym.synonym)
            self.Qline_ref.setText(self.myPNSynonym.taxon_ref)
            self.Qline_search.setText('')
            self.frame_treeview.setVisible(False)
            self.ui_addname.setMaximumHeight(1)
            self.Qline_name.setFocus()
        self.Qline_search.returnPressed.connect(self.search_for_text)
        self.Qline_name.textChanged.connect (self.valid_newname)
        self.Qline_search.textChanged.connect (self.valid_newname)
        self.Qcombobox.activated.connect(self.valid_newname)
        selection = self.Qtreeview_search.selectionModel()
        selection.selectionChanged.connect(self.valid_newname)   
        self.button_ok.clicked.connect (self.accept) 
        self.button_cancel.clicked.connect (self.close)
        self.valid_newname()

    def show(self):
        self.setting_ui()
        self.ui_addname.show()
        self.ui_addname.exec()
        
    def close(self):
        #self.button_click.emit(0)
        self.ui_addname.close()

    def valid_newname(self):
        txt_item = self.Qline_name.text().strip()
        txt_category = self.Qcombobox.currentText().strip()         
        if self.myPNSynonym.resolved:
            flag = not (self.myPNSynonym.synonym == txt_item and self.myPNSynonym.category ==txt_category)
            self.button_ok.setEnabled(flag)
            return



        model = self.Qtreeview_search.model()

        flag = False
        if self.myPNSynonym.resolved:
            flag = len(txt_item)>3
        elif model is not None:
            c_index = self.Qtreeview_search.currentIndex()
            row_item = c_index.row()
            if c_index.parent().isValid():
                row_item = c_index.parent().row()
            try:
                new_taxonref = model.item(row_item,0).data(0)
                self.Qline_ref.setText(new_taxonref)
            except:
                pass          
            flag = len(txt_item)>3 and model.item(row_item) is not None
        self.button_ok.setEnabled(flag)

    def search_for_text (self):
        taxa = self.Qline_search.text().strip()
        sql_query = "SELECT taxonref, score, a.id_taxonref, synonym FROM taxonomy.pn_taxa_searchname('" + taxa +"', 0.5) a"
        sql_query += "\nLEFT JOIN taxonomy.taxa_synonym b ON a.id_taxonref = b.id_taxonref"
        #treeview_search = self.treeview_search
        model = self.Qtreeview_search.model()
        model.setRowCount(0)
        query = QtSql.QSqlQuery (sql_query)
        record = query.record()
        tab_header = []
        for i in range(record.count()-1):
            tab_header.append(record.fieldName(i))
        column_index_idtaxonref = len(tab_header) -1 
        while query.next():
            ls_item_taxonref = model.findItems(str(query.value('id_taxonref')),Qt.MatchExactly,column_index_idtaxonref)
            if not ls_item_taxonref:
                model.appendRow([QtGui.QStandardItem(str(query.value(x))) for x in tab_header])
                ls_item_taxonref = model.findItems(str(query.value('id_taxonref')),Qt.MatchExactly,column_index_idtaxonref)
                row = ls_item_taxonref[0].row()
            if query.value('score') < 50:
                #model.setData(model.index(i, 0), QtGui.QBrush(Qt.red), Qt.ForegroundRole)
                model.setData(model.index(row, 1), QtGui.QBrush(QtGui.QColor(255, 0, 0)), Qt.ForegroundRole)
            if query.value('synonym') is not None:
                model.item(row).appendRow ([QtGui.QStandardItem(query.value('synonym')), ])
        model.setHorizontalHeaderLabels(tab_header)
        self.Qtreeview_search.hideColumn(column_index_idtaxonref)
        self.Qtreeview_search.header().setStretchLastSection(False)
        self.Qtreeview_search.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.Qtreeview_search.header().setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)
        self.Qtreeview_search.resizeColumnToContents(1)

    def accept(self):
        self.updated = False
        new_synonym = self.Qline_name.text().strip()
        new_category = self.Qcombobox.currentText()
        new_taxonref = self.Qline_ref.text().strip()
        idsynonym = self.myPNSynonym.idsynonym
        if self.myPNSynonym.resolved:
            idtaxonref = self.myPNSynonym.idtaxonref
        else:
            try :
                model = self.Qtreeview_search.model()
                if self.Qtreeview_search.currentIndex().parent().row() >= 0:
                    row_item = self.Qtreeview_search.currentIndex().parent().row()
                else:
                    row_item = self.Qtreeview_search.currentIndex().row()

                idtaxonref = int(model.item(row_item,2).data(0))
            except:
                idtaxonref = 0
        if idsynonym > 0:
            #edit mode
            #return if nothing has changed
            if new_synonym == self.myPNSynonym.synonym and new_category == self.myPNSynonym.category:
                self.ui_addname.close()
                return True
            sql_query = "SELECT taxonomy.pn_taxa_edit_synonym ('" +new_synonym + "','" + new_category +"',0," + str(idsynonym) +")"
        else:
            #add mode
            sql_query = "SELECT taxonomy.pn_taxa_edit_synonym ('" +new_synonym + "','" + new_category +"'," + str(idtaxonref) +")"
        result = QtSql.QSqlQuery (sql_query)

        #check for errors code (cf. postgresql function taxonomy.pn_taxa_edit_synonym)
        code_error = result.lastError().nativeErrorCode ()
        msg = ''
        if len(code_error) == 0:
            result.next()
            id_item = result.value(0)
            self.myPNSynonym.synonym = new_synonym
            self.myPNSynonym.category = new_category
            self.myPNSynonym.taxon_ref = new_taxonref                                    
            self.myPNSynonym.id_taxonref = idtaxonref            
            self.myPNSynonym.id_synonym = id_item
            self.ui_addname.close()
            #self.button_click.emit(self,1)
            self.updated = True
            return True
        elif code_error in ['23505', '23000']:
            msg = "Error: Duplicate key value violates unique constraint"
        else:
            msg = "Error: invalid parameters"
        t = result.lastError().databaseText() .split('CONTEXT')
        msg += "\n" + t [0]    
        QtWidgets.QMessageBox.critical(self.ui_addname, "Database error", msg, QtWidgets.QMessageBox.Ok)
        return False


