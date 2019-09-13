import SimpleITK as sitk
import numpy as np
import nibabel as nib
import os
import cv2
import vtk

def merge(image_data,label_data):#画标签
    merge_data = []
    for i in range(len(image_data)):
        img = image_data[i].astype(np.uint8)
        mask_img = label_data[i]
        x, y = np.where(mask_img != 0)
        img[x[:], y[:], 0] = 0
        img[x[:], y[:], 1] = 0
        img[x[:], y[:], 2] = 255
        merge_data.append(img)
    return np.array(merge_data)


def nii2mhd(nii_file, save_file="temp/from_nii.mhd"):
    input_type = nii_file.split('.')[-1]
    if input_type != 'nii' and input_type != 'gz' :
        print('ERROR: input file is not in nii format')
        return ''
    elif input_type == 'mhd':
        return nii_file
    save_dir = os.path.dirname(save_file)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    img = nib.load(nii_file)
    slices = np.transpose(img.dataobj, (2, 0, 1))
    spacing = np.diag(img.affine)[:3]
    sitk_img = sitk.GetImageFromArray(slices, isVector=False)
    sitk_img.SetSpacing(spacing)
    sitk_img.SetOrigin((0, 0, 0))
    sitk.WriteImage(sitk_img, save_file)
    return save_file


def clip(img, hu_min=0, hu_max=1000):
    image = np.array(img)
    image[image < hu_min] = hu_min
    image[image > hu_max] = hu_max
    image = (image-hu_min)/(hu_max-hu_min)*255
    return np.array([cv2.cvtColor(i.astype(np.uint8), cv2.COLOR_GRAY2BGR) for i in image])


def genActor(reader, extract_value, render_color):
    colors = vtk.vtkNamedColors()
    colors.SetColor("labelColor", [0, 0, 255, 255])

    boneExtractor = vtk.vtkMarchingCubes()
    boneExtractor.SetInputConnection(reader.GetOutputPort())
    boneExtractor.SetValue(0, extract_value)

    boneStripper = vtk.vtkStripper()
    boneStripper.SetInputConnection(boneExtractor.GetOutputPort())

    boneMapper = vtk.vtkPolyDataMapper()
    boneMapper.SetInputConnection(boneStripper.GetOutputPort())
    boneMapper.ScalarVisibilityOff()

    bone = vtk.vtkActor()
    bone.SetMapper(boneMapper)
    bone.GetProperty().SetDiffuseColor(colors.GetColor3d(render_color))

    return bone
