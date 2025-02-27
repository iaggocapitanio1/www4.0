"""
Created in Sep 2022
supports the following Python versions: 3.6, 3.7, 3.8, 3.9, 3.10
Developer: Iaggo Capitanio.
"""
from typing import Union, List, Optional
from pathlib import Path
import os
from pdf2image import convert_from_path
from PIL.PpmImagePlugin import PpmImageFile
import cv2
import numpy
import pandas
import pytesseract
import img2pdf
import io
from django.db.models import QuerySet
from django.core.files.base import ContentFile


def get_tesseract_path() -> Path:
    """
    This function aims to get the path that points to the tesseract executable. This function works in both operational
    system: Linux and Windows.
    @return:
    """
    import subprocess
    import os

    def find_tesseract(finder: str = "which") -> str:
        """
        Searches for the tesseract executable using the specified command to locate executables in the system. It
        relies on a terminal command to find the path to the 'tesseract' executable.

        For Linux, the default command is 'which', and for Windows, it is 'where'. The function returns the full path to
        the tesseract executable as a string.

        Args:
            finder (str, optional): Command used to find the executable in the system. Defaults to 'which' for Linux.

        Returns:
            str: Full path to the tesseract executable as a string.

        Example:
            tesseract_path = find_tesseract()
        """
        output = subprocess.Popen([finder, 'tesseract'], stdout=subprocess.PIPE)
        return output.communicate()[0].decode("utf-8")

    if os.name == 'nt':
        result = find_tesseract(finder='where')
    elif os.name == 'posix':
        result = find_tesseract()
    else:
        raise OSError('Invalid OS')
    tesseract_path: Path = Path(result.strip())
    return tesseract_path


def get_tesseract_dir() -> Path:
    """
    Retrieves the directory containing the tesseract executable.

    Returns:
        Path: A Path object representing the directory containing the tesseract executable.

    Example:
        tesseract_dir = get_tesseract_dir()
    """
    tesseract_path: Path = get_tesseract_path()
    return tesseract_path.parent


pytesseract.pytesseract.tesseract_cmd = get_tesseract_path()


def normalize_name(name: str) -> str:
    """
    Normalizes a given name string by removing leading and trailing white spaces, replacing
    internal white spaces with underscores, and removing any trailing underscores.

    Args:
        name (str): The input name string to be normalized.

    Returns:
        str: The normalized name string.

    Example:
        normalized_name = normalize_name("  Example  Name  ")
    """
    name = name.strip()  # remove the tab character and white spaces
    name = name.replace(' ', '_').strip()  # if there is some name with white space, normalize it replacing with '_'
    name_list: list = name.split('_')
    return '_'.join([word for word in name_list if word][:-1])


def convert_str_to_path(path: Union[Path, str]) -> Path:
    """
    Converts a given path, which can be a string or a Path object, into a resolved Path object.

    Args:
        path (Union[Path, str]): The input path as a string or a Path object.

    Returns:
        Path: The resolved Path object.

    Example:
        resolved_path = convert_str_to_path("path/to/directory")
    """
    if isinstance(path, str):
        return Path(path).resolve()
    return path.resolve()


def extract_tag_name_from_image(img: Union[str, Path, numpy.ndarray]) -> str:
    """
    Extracts the tag name from a specific image. The image should follow certain size and dpi standards. The function
    crops the image according to the specified matrix and extracts the string using the tesseract package.

    Args:
        img (Union[str, Path, np.ndarray]): The target image, either as a file path (str or Path) or as a numpy array.

    Returns:
        str: The tag name contained in the image.

    Example:
        tag_name = extract_tag_name_from_image("path/to/image.jpg")
    """
    if isinstance(img, Path) or isinstance(img, str):
        img = cv2.imread(img.__str__())
    crop = img[540:670, 70:1600]  # [rows, columns]
    custom_config = r'--oem 3 --psm 6'  # Adding custom options
    result = pytesseract.image_to_string(crop, config=custom_config)
    return normalize_name(name=result)


def extract_tag_value_from_dataframe(dataframe: pandas.DataFrame, tag_name: str,
                                     column_header_tag_name: str = 'REF PEÇA (A)',
                                     column_header_tag_value: str = 'ETIQ (H)') -> int:
    """
    Searches for a tag name in a given DataFrame and returns the corresponding value found.

    Args:
        dataframe (pd.DataFrame): The reference DataFrame to search. tag_name (str): The tag name to find.
        column_header_tag_name (str, optional): The column header that contains the tag name. Defaults to
        'REF PEÇA (A)'.
        column_header_tag_value (str, optional): The column header that contains the tag value. Defaults to 'ETIQ (H)'.

    Returns:
        int: The value found corresponding to the tag name.

    Example:
        tag_value = extract_tag_value_from_dataframe(dataframe, "tag_name")
    """
    row = dataframe[dataframe[column_header_tag_name] == tag_name]
    tag_value: int = int(row[column_header_tag_value].iloc[0])
    return tag_value


def draw_tags(images: List[numpy.ndarray], tags: List[int], output_folder: Path) -> None:
    """
    Draws tags on the given images and saves the annotated images to the specified output folder.

    Args:
        images (List[np.ndarray]): A list of images in numpy.ndarray format.
        tags (List[int]): A list of integer tags corresponding to each image.
        output_folder (Path): The output folder where the annotated images will be saved.

    Example:
        draw_tags(images, tags, output_folder)
    """
    for tag, image in zip(tags, images):
        cv2.putText(image, str(tag), (1700, 650), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 4)
        cv2.imwrite(output_folder.joinpath(f"{tag}.png").__str__(), image)


def get_tags_value_from_excel(excel_path: Union[str, Path], tags: list, sheet_name: str = 'DATA - Paineis') -> \
        List[int]:
    """
    Retrieves the corresponding tag values from the given Excel file for the provided list of tag names.

    Args:
        excel_path (Union[str, Path]): The path to the Excel file containing the tag data.
        tags (List[str]): A list of tag names to search for in the Excel file.
        sheet_name (str, optional): The name of the sheet in the Excel file containing the tag data. Defaults to
        'DATA - Paineis'.

    Returns:
        List[int]: A list of integer tag values corresponding to the provided tag names.

    Example:
        tag_values = get_tags_value_from_excel(excel_path, tags, sheet_name)
    """

    dataframe = pandas.read_excel(excel_path, sheet_name=sheet_name)
    dataframe = dataframe.assign(tag='')
    return [extract_tag_value_from_dataframe(dataframe=dataframe, tag_name=tag_name) for tag_name in tags]


def create_pdf_with_tags(images: List[numpy.ndarray], tags: List[int], pdf_filename: str, save: bool = False) -> \
        Union[None, list]:
    """
    Creates a PDF file containing the given images with tags drawn on them.

    The function takes a list of images as numpy arrays and a corresponding list of integer tags.
    For each image, it draws the corresponding tag as text on the image and then saves the
    modified images as a single PDF file.

    Args:
        images (List[numpy.ndarray]): A list of images as numpy arrays.
        tags (List[int]): A list of integer tags corresponding to each image in the 'images' list.
        pdf_filename (str): The filename for the output PDF file.
        save (bool): Save to a  file.

    Returns:
        None
    """
    buffer_list = []

    for tag, image in zip(tags, images):
        cv2.putText(image, str(tag), (1700, 650), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 4)
        is_success, buffer = cv2.imencode(".png", image)
        if is_success:
            image_in_memory = io.BytesIO(buffer)
            buffer_list.append(image_in_memory)
    if save:
        with open(os.path.join(pdf_filename), "wb") as f:
            f.write(img2pdf.convert(buffer_list))
        return
    return img2pdf.convert(buffer_list)


def save_result(tag_id: str, pdf: ContentFile, created: bool) -> None:
    from tags.models import TagResult, Tag
    tags: QuerySet = Tag.objects.filter(id=tag_id)
    if tags.exists():
        tag = tags.first()
        if created:
            obj = TagResult(tag=tag, pdf=pdf)
            obj.save()
        else:
            objs: QuerySet = TagResult.objects.filter(tag=tag)
            if objs.exists():
                instance: TagResult = objs.first()
                instance.pdf.delete()
                instance.pdf = pdf
                instance.tag = tag
                instance.save()


def process(pdf_path: Union[Path, str], excel_path: Union[Path, str], tag_id: str, created: bool,
            output_path: Optional[Union[str, Path]] = None) -> None:
    """
    Processes a PDF file, extracts tag names from images, retrieves tag values from an Excel file, and draws tags on
    images.

    This function takes a PDF file containing images, converts the images to digital format, extracts tag names from the
    images, retrieves the corresponding tag values from an Excel file, and draws the tags on the images. The modified
    images are saved in the specified output folder.

    Args:
        pdf_path (Union[Path, str]): The path to the PDF file containing the images.
        excel_path (Union[Path, str]): The path to the Excel file containing the tag data.
        tag_id (str): Tag id.
        created (bool): created tag.
        output_path (Optional[Union[str, Path]], optional): The path to the folder where the modified images will be
        saved. If not provided, a folder named 'output' will be created in the same directory as the PDF file. Defaults
        to None.

    Example:
        process(pdf_path, excel_path, output_path)

    """
    pdf_path = convert_str_to_path(pdf_path)
    excel_path = convert_str_to_path(excel_path)
    if output_path is None:
        # output_path = Path(os.path.join(pdf_path.parent, 'output'))
        output_path = f"{pdf_path.stem}_output.pdf"
    # os.makedirs(output_path, exist_ok=True)
    original_images: List[PpmImageFile] = convert_from_path(pdf_path=pdf_path, dpi=500)
    original_digital_images = [numpy.asarray(image) for image in original_images]
    for img in original_digital_images:
        cv2.rectangle(img, (1630, 540), (1955, 690), (0, 0, 0), -1)
    original_tags: List[str] = [extract_tag_name_from_image(image) for image in original_digital_images]
    tags_value: List[int] = get_tags_value_from_excel(excel_path=excel_path, tags=original_tags)
    # draw_tags(images=original_digital_images, tags=tags_value, output_folder=output_path)
    buffer_list = create_pdf_with_tags(images=original_digital_images, tags=tags_value, pdf_filename=output_path)
    pdf_content = ContentFile(buffer_list, name=output_path)
    save_result(tag_id=tag_id, pdf=pdf_content, created=created)
