import requests
from flask import current_app, json
from notifications_utils.template import LetterPreviewTemplate

from app import current_service


class TemplatePreview:
    @classmethod
    def from_database_object(
        cls,
        template,
        filetype,
        values=None,
        date=None,
        page=None,
    ):
        letter_preview_template = LetterPreviewTemplate(
            template,
            values,
            letter_contact_block=template.get('reply_to_text', ''),
            admin_base_url='http://localhost:6013',
            logo_file_name=logos.get(
                current_service['dvla_organisation']
            ).raster,
            date=date,
        )
        resp = requests.post(
            '{}/preview.html.{}{}'.format(
                current_app.config['TEMPLATE_PREVIEW_API_HOST'],
                filetype,
                '?page={}'.format(page) if page else '',
            ),
            json={"html": str(letter_preview_template)},
            headers={'Authorization': 'Token {}'.format(current_app.config['TEMPLATE_PREVIEW_API_KEY'])}
        )
        return (resp.content, resp.status_code, resp.headers.items())

    @classmethod
    def from_utils_template(cls, template, filetype, page=None, date=None):
        return cls.from_database_object(
            template._template,
            filetype,
            template.values,
            page=page,
            date=date,
        )


def get_page_count_for_letter(template, values=None):

    if template['template_type'] != 'letter':
        return None

    page_count, _, _ = TemplatePreview.from_database_object(template, 'json', values)
    page_count = json.loads(page_count.decode('utf-8'))['count']

    return page_count
