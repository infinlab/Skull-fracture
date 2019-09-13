# -*- coding: UTF-8 -*-
import sys
from mainUI import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import *
import math
from PyQt5.QtCore import Qt, QEvent
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage, QPixmap
from utils import *
from PyQt5.QtWidgets import QMessageBox

from PyQt5.QtWidgets import  QGraphicsScene, QGraphicsPixmapItem, QGraphicsView

class mywindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(mywindow, self).__init__()
        self.setupUi(self)
        self.init_var()
        self.init_ui()

    def init_var(self):
        self.dirPath = ''
        self.slice_idx = 0
        self.samples = []
        self.hasLabel = False
        self.showLabel = False
        self.current_image_path = ''
        self.current_label_path = ''
        self.current_label = None # 原始标签
        self.current_image = None # 原始图片
        self.current_data = None # 指针
        self.current_clip = None # 窗口图片
        self.current_merge = None # 合并图片

        self.boneActor = None
        self.labelActor = None
        self.outlineActor = None

        self.HU2dmin = 0
        self.HU2dmax = 1000
        self.HU3d = 500
        self.HUMIN = -3000
        self.HUMAX = 3000

    def message(self,item):

        self.hasLabel = False
        self.showLabel = False

        self.current_image_path, self.current_label_path = '',''
        for i in self.samples:
            if item.text() in i[0]:
                self.current_image_path, self.current_label_path = i[0],i[1]
                if len(i[1])>0:
                    self.hasLabel = True

        if self.current_image_path != '':
            try:
                #读取文件放到中间两个框框
                print('selected: ', self.current_image_path)
                self.current_image = np.transpose(nib.load(self.current_image_path).dataobj,(2,0,1))
                if self.hasLabel:
                    self.current_label = np.transpose(nib.load(self.current_label_path).dataobj, (2, 0, 1))
                self.current_clip = clip(self.current_image, self.HU2dmin, self.HU2dmax)
                self.current_data = self.current_clip
                self.show2d()
                self.clear3d()
                self.show3d()
            except Exception as e:
                print(e)

        img = nib.load(self.current_image_path)
        pieces = str(img.header).split('\n')
        l = []
        for p in pieces:
            if '<class' not in p and 'magic' not in p and 'pixdim' not in p and 'slice_start' not in p and ':' in p:
                l.append(p)
        self.NIImessage.setText('\n'.join(l))

        if self.hasLabel:
            self.textBrowser.setText("骨窗示：顶骨见多发线状低密度影，骨皮质不连续，可见断端向内移位，余颅骨骨质密度正常，未见明确骨折线影。")
        else:
            self.textBrowser.setText("颅骨骨质密度正常，未见明确骨折线影。")


    def help(self):
        vbox = QVBoxLayout()  # 纵向布局
        dialog = QDialog()
        dialog.setWindowTitle(u"说明")
        label = QLabel(self)
        pix = QPixmap('resource/help.jpg')
        label.setPixmap(pix)
        vbox.addWidget(label)
        dialog.setLayout(vbox)
        dialog.setWindowModality(Qt.ApplicationModal)
        dialog.exec_()

    def table(self):

        self.dirPath = QFileDialog.getExistingDirectory(self)

        if len(self.dirPath) > 0:
            print('selected: ', self.dirPath)
            self.filelist = os.listdir(self.dirPath)

            test_sample = []
            test_path = self.dirPath
            for instance in os.listdir(test_path):
                instance_path = os.path.join(test_path, instance)
                files = [os.path.join(instance_path, i) for i in os.listdir(instance_path)]
                if len(files) > 0:
                    test_sample.append(files)

            self.samples = [[test_sample[i][0], ''] if len(test_sample[i]) == 1 else [test_sample[i][1], test_sample[i][0]] for i
                in range(len(test_sample))]

        _translate = QtCore.QCoreApplication.translate

        self.List.clear()
        for i in self.samples:
            if len(i[1]) == 0:
                item = QtWidgets.QListWidgetItem(QtGui.QIcon('resource/green.png'),
                                                 _translate("MainWindow", i[0].split(os.path.sep)[-2]))
                self.List.addItem(item)
            else:
                item = QtWidgets.QListWidgetItem(QtGui.QIcon('resource/red.png'),
                                                 _translate("MainWindow", i[0].split(os.path.sep)[-2]))
                self.List.addItem(item)

        # for i in self.samples:
        #     item = QtWidgets.QListWidgetItem()
        #     item.setText(_translate("MainWindow", i[0].split(os.path.sep)[-2]))
        #     self.List.addItem(item)
        #     print(i)


    def show2d(self):
        self.statusBar().showMessage("showLabel: {}".format(self.showLabel))
        self.current_data = self.current_merge if self.showLabel else self.current_clip
        img = self.current_data[self.slice_idx]
        # img = img[:,::-1,:]
        x = img.shape[1]
        y = img.shape[0]
        size = self.view2d.size()
        zoomscale = max([size.height(), size.width()]) / x  # 图片放缩尺度
        qimg = QImage(img, x, y, QImage.Format_RGB888)
        qpix = QPixmap.fromImage(qimg)
        item = QGraphicsPixmapItem(qpix)
        item.setScale(zoomscale)
        scene = QGraphicsScene()
        scene.addItem(item)
        self.view2d.setScene(scene)
        self.view2d.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view2d.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def show3d(self):
        bone_reader = vtk.vtkMetaImageReader()
        bone_reader.SetFileName(nii2mhd(self.current_image_path,save_file="temp/bone.mhd"))
        self.boneActor = genActor(bone_reader, self.HU3d, "Ivory")

        if self.hasLabel:
            label_reader = vtk.vtkMetaImageReader()
            label_reader.SetFileName(nii2mhd(self.current_label_path, save_file="temp/label.mhd"))
            self.labelActor = genActor(label_reader, 1, "labelColor")

        outlineData = vtk.vtkOutlineFilter()
        outlineData.SetInputConnection(bone_reader.GetOutputPort())
        mapOutline = vtk.vtkPolyDataMapper()
        mapOutline.SetInputConnection(outlineData.GetOutputPort())
        self.outlineActor = vtk.vtkActor()
        self.outlineActor.SetMapper(mapOutline)
        self.outlineActor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Red"))

        aCamera = vtk.vtkCamera()
        aCamera.SetViewUp(0, 0, 1)
        aCamera.SetPosition(0, -1, 0)
        aCamera.SetFocalPoint(0, 0, 0)
        aCamera.ComputeViewPlaneNormal()
        aCamera.Azimuth(30.0)
        aCamera.Elevation(30.0)
        aCamera.Dolly(1.1)

        self.ren.AddActor(self.boneActor)
        if self.showLabel:
            self.ren.AddActor(self.labelActor)
        self.ren.AddActor(self.outlineActor)
        self.ren.SetActiveCamera(aCamera)
        self.ren.ResetCamera()
        self.ren.ResetCameraClippingRange()
        self.view3d.GetRenderWindow().Render()

    def show3d_label(self):
        if self.showLabel:
            self.ren.AddActor(self.labelActor)
        else:
            try:
                self.ren.RemoveActor(self.labelActor)
            except Exception as e:
                pass
        self.view3d.GetRenderWindow().Render()

    def clear3d(self):
        try:
            self.ren.RemoveActor(self.labelActor)
            self.ren.RemoveActor(self.boneActor)
            self.ren.RemoveActor(self.outlineActor)
        except Exception as e:
            pass

    def init_3drender(self):
        self.view3d.close()
        self.horizontalLayout.removeWidget(self.view3d)
        self.view3d = QVTKRenderWindowInteractor(self.centralwidget)
        self.view3d.setObjectName("vtkWidget")
        self.horizontalLayout.addWidget(self.view3d)
        self.ren = vtk.vtkRenderer()
        self.view3d.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.view3d.GetRenderWindow().GetInteractor()
        colors = vtk.vtkNamedColors()
        colors.SetColor("BkgColor", [0, 0, 0, 255])
        self.ren.SetBackground(colors.GetColor3d("BkgColor"))
        self.iren.Initialize()


    def init_2drender(self):
        self.view2d.close()
        self.horizontalLayout.removeWidget(self.view2d)
        self.view2d = MyView(self.centralwidget)
        self.view2d.setWindow(self)
        self.view2d.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view2d.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view2d.horizontalScrollBar().disconnect()
        self.view2d.verticalScrollBar().disconnect()
        self.view2d.setObjectName("view2d")
        self.horizontalLayout.addWidget(self.view2d)

    def help(self):
        # QMessageBox.about(self, "使用说明",  QtGui.QIcon('resource/help.jpg'))

        vbox = QVBoxLayout()
        msgBox = QDialog()
        msgBox.setWindowIcon(QtGui.QIcon('resource/logo.jpg'))
        msgBox.setWindowTitle("说明")
        label = QLabel(self)
        pix = QPixmap('resource/help.jpg')
        label.setPixmap(pix)
        vbox.addWidget(label)
        msgBox.setLayout(vbox)
        msgBox.setWindowModality(Qt.ApplicationModal)
        msgBox.exec_()

    def changeSlider1(self, value):
        self.HU2dmin = value
        if self.current_clip is not None:
            self.current_clip = clip(self.current_image, self.HU2dmin, self.HU2dmax)
            self.show2d()

    def changeSlider2(self, value):
        self.HU2dmax = value
        if self.current_clip is not None:
            self.current_clip = clip(self.current_image, self.HU2dmin, self.HU2dmax)
            self.show2d()

    def init_ui(self):
        # self.pushButton_open.clicked.connect(self.choosePhoto)
        # self.pushButton_detect.clicked.connect(self.show_label)
        self.action_open.triggered.connect( self.table)
        self.action_help.triggered.connect(self.help)
        self.List.itemClicked.connect(self.message)  # 点击文件名触发显示NII信息
        self.List.clear()
        self.init_2drender()
        self.init_3drender()
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 1)

        self.view2d.setStyleSheet('''background-color:rgb(0, 0, 0);border-width:2px;border-color: rgb(230,230,250); ''')
        self.view3d.setStyleSheet('''background-color:rgb(0, 0, 0);border-width:2px;border-color: rgb(230,230,250); ''')
        self.NIImessage.setStyleSheet('''background-color:rgb(105, 105, 105);border-radius: 5px; color:rgb(255,255,255); ''')
        self.List.setStyleSheet('''background-color:rgb(105, 105, 105);border-radius: 5px;  color:rgb(255,255,255);''')
        self.textBrowser.setStyleSheet('''background-color:rgb(255, 255, 255);  color:rgb(0,0,0);''')
        self.setStyleSheet('''background-color:rgb(207, 207, 207);border-radius: 5px;  color:rgb(0,0,0);''')

        self.setWindowIcon(QtGui.QIcon('./resource/logo.jpg'))

        self.Slider1.valueChanged[int].connect(self.changeSlider1)
        self.Slider2.valueChanged[int].connect(self.changeSlider2)
        self.Slider1.setMinimum(-3000)
        self.Slider2.setMinimum(-3000)
        self.Slider1.setMaximum(3000)
        self.Slider2.setMaximum(3000)
        self.Slider1.setValue(0)
        self.Slider2.setValue(1000)

        # screen = QDesktopWidget().screenGeometry()
        # self.setGeometry(0, 0, screen.width(), screen.height())

class MyView(QGraphicsView):
    def __init__(self, parent):
        super(MyView,self).__init__(parent)
        self.window = None

    def setWindow(self, w):
        self.window = w

    def wheelEvent(self,event):
            # print("点鼠标. 坐标值:", event.x(), event.y())
            '''Zoom In/Out with CTRL + mouse wheel'''
            if event.modifiers() == Qt.ControlModifier:
                s = math.pow(2.0, event.angleDelta().y() / 240.0)
                x, y = event.x(), event.y()
                c_x, c_y = self.size().width()//2, self.size().height()//2
                # print(c_x, c_y)
                self.scale(s,s)

            elif self.window.current_data is not None:
                # return QGraphicsView.wheelEvent(self, event)
                self.window.slice_idx += 1 if event.angleDelta().y() > 0 else -1
                self.window.slice_idx = max(0,min(self.window.slice_idx, len(self.window.current_data)-1))
                self.window.show2d()

    def mousePressEvent(self,e):
        if(e.buttons()==QtCore.Qt.RightButton):
            if self.window.hasLabel==True:
                self.window.showLabel = not self.window.showLabel
                self.window.current_merge = merge(self.window.current_clip, self.window.current_label)
                self.window.show2d()
                self.window.show3d_label()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = mywindow()
    # MainWindow.show()
    MainWindow.showMaximized()
    # MainWindow.showFullScreen()
    sys.exit(app.exec_())