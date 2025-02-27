from utilities.tesseract import process
from celery import shared_task
from typing import Union, Optional
from pathlib import Path


@shared_task()
def process_task(pdf_path: Union[Path, str], excel_path: Union[Path, str], tag_id: str, created: bool,
                 output_path: Optional[Union[str, Path]] = None):
    return process(pdf_path=pdf_path, excel_path=excel_path, tag_id=tag_id, created=created, output_path=output_path)
