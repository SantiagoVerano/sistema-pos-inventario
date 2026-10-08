# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'inventario_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTableView, QVBoxLayout, QWidget)

class Ui_InventarioWindow(object):
    def setupUi(self, InventarioWindow):
        if not InventarioWindow.objectName():
            InventarioWindow.setObjectName(u"InventarioWindow")
        InventarioWindow.resize(900, 600)
        self.verticalLayoutInventario = QVBoxLayout(InventarioWindow)
        self.verticalLayoutInventario.setObjectName(u"verticalLayoutInventario")
        self.horizontalLayoutKpis = QHBoxLayout()
        self.horizontalLayoutKpis.setObjectName(u"horizontalLayoutKpis")
        self.frmKpiTotal = QFrame(InventarioWindow)
        self.frmKpiTotal.setObjectName(u"frmKpiTotal")
        self.frmKpiTotal.setFrameShape(QFrame.StyledPanel)
        self.verticalLayoutKpi1 = QVBoxLayout(self.frmKpiTotal)
        self.verticalLayoutKpi1.setObjectName(u"verticalLayoutKpi1")
        self.lblTituloKpi1 = QLabel(self.frmKpiTotal)
        self.lblTituloKpi1.setObjectName(u"lblTituloKpi1")

        self.verticalLayoutKpi1.addWidget(self.lblTituloKpi1)

        self.lblValorKpi1 = QLabel(self.frmKpiTotal)
        self.lblValorKpi1.setObjectName(u"lblValorKpi1")

        self.verticalLayoutKpi1.addWidget(self.lblValorKpi1)


        self.horizontalLayoutKpis.addWidget(self.frmKpiTotal)

        self.frmKpiStockBajo = QFrame(InventarioWindow)
        self.frmKpiStockBajo.setObjectName(u"frmKpiStockBajo")
        self.frmKpiStockBajo.setFrameShape(QFrame.StyledPanel)
        self.verticalLayoutKpi2 = QVBoxLayout(self.frmKpiStockBajo)
        self.verticalLayoutKpi2.setObjectName(u"verticalLayoutKpi2")
        self.lblTituloKpi2 = QLabel(self.frmKpiStockBajo)
        self.lblTituloKpi2.setObjectName(u"lblTituloKpi2")

        self.verticalLayoutKpi2.addWidget(self.lblTituloKpi2)

        self.lblValorKpi2 = QLabel(self.frmKpiStockBajo)
        self.lblValorKpi2.setObjectName(u"lblValorKpi2")

        self.verticalLayoutKpi2.addWidget(self.lblValorKpi2)


        self.horizontalLayoutKpis.addWidget(self.frmKpiStockBajo)

        self.frmKpiAgotados = QFrame(InventarioWindow)
        self.frmKpiAgotados.setObjectName(u"frmKpiAgotados")
        self.frmKpiAgotados.setFrameShape(QFrame.StyledPanel)
        self.verticalLayoutKpi3 = QVBoxLayout(self.frmKpiAgotados)
        self.verticalLayoutKpi3.setObjectName(u"verticalLayoutKpi3")
        self.lblTituloKpi3 = QLabel(self.frmKpiAgotados)
        self.lblTituloKpi3.setObjectName(u"lblTituloKpi3")

        self.verticalLayoutKpi3.addWidget(self.lblTituloKpi3)

        self.lblValorKpi3 = QLabel(self.frmKpiAgotados)
        self.lblValorKpi3.setObjectName(u"lblValorKpi3")

        self.verticalLayoutKpi3.addWidget(self.lblValorKpi3)


        self.horizontalLayoutKpis.addWidget(self.frmKpiAgotados)


        self.verticalLayoutInventario.addLayout(self.horizontalLayoutKpis)

        self.horizontalLayoutFiltrosInventario = QHBoxLayout()
        self.horizontalLayoutFiltrosInventario.setObjectName(u"horizontalLayoutFiltrosInventario")
        self.txtBuscarInventario = QLineEdit(InventarioWindow)
        self.txtBuscarInventario.setObjectName(u"txtBuscarInventario")

        self.horizontalLayoutFiltrosInventario.addWidget(self.txtBuscarInventario)

        self.cmbFiltroAlmacenCategoria = QComboBox(InventarioWindow)
        self.cmbFiltroAlmacenCategoria.setObjectName(u"cmbFiltroAlmacenCategoria")

        self.horizontalLayoutFiltrosInventario.addWidget(self.cmbFiltroAlmacenCategoria)

        self.btnGenerarAjuste = QPushButton(InventarioWindow)
        self.btnGenerarAjuste.setObjectName(u"btnGenerarAjuste")

        self.horizontalLayoutFiltrosInventario.addWidget(self.btnGenerarAjuste)


        self.verticalLayoutInventario.addLayout(self.horizontalLayoutFiltrosInventario)

        self.tblInventarioStock = QTableView(InventarioWindow)
        self.tblInventarioStock.setObjectName(u"tblInventarioStock")

        self.verticalLayoutInventario.addWidget(self.tblInventarioStock)


        self.retranslateUi(InventarioWindow)

        QMetaObject.connectSlotsByName(InventarioWindow)
    # setupUi

    def retranslateUi(self, InventarioWindow):
        self.lblTituloKpi1.setText(QCoreApplication.translate("InventarioWindow", u"Total Productos", None))
        self.lblValorKpi1.setText(QCoreApplication.translate("InventarioWindow", u"0", None))
        self.lblTituloKpi2.setText(QCoreApplication.translate("InventarioWindow", u"Stock Bajo", None))
        self.lblValorKpi2.setText(QCoreApplication.translate("InventarioWindow", u"0", None))
        self.lblTituloKpi3.setText(QCoreApplication.translate("InventarioWindow", u"Agotados", None))
        self.lblValorKpi3.setText(QCoreApplication.translate("InventarioWindow", u"0", None))
        self.txtBuscarInventario.setPlaceholderText(QCoreApplication.translate("InventarioWindow", u"Filtrar existencias por nombre o c\u00f3digo...", None))
        self.btnGenerarAjuste.setText(QCoreApplication.translate("InventarioWindow", u"Registrar Ajuste / Movimiento", None))
        pass
    # retranslateUi

