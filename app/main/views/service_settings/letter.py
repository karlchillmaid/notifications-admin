# from flask import (
#     abort,
#     current_app,
#     flash,
#     redirect,
#     render_template,
#     request,
#     session,
#     url_for,
# )
from flask_login import login_required
# from notifications_python_client.errors import HTTPError
# from notifications_utils.field import Field
# from notifications_utils.formatters import formatted_list

# from app import (
#     billing_api_client,
#     current_service,
#     email_branding_client,
#     inbound_number_client,
#     organisations_client,
#     service_api_client,
#     user_api_client,
#     zendesk_client,
# )
from app.main import main
# from app.main.forms import (
#     ConfirmPasswordForm,
#     FreeSMSAllowance,
#     InternationalSMSForm,
#     LetterBranding,
#     LinkOrganisationsForm,
#     OrganisationTypeForm,
#     RenameServiceForm,
#     RequestToGoLiveForm,
#     ServiceEditInboundNumberForm,
#     ServiceInboundNumberForm,
#     ServiceLetterContactBlockForm,
#     ServiceReplyToEmailForm,
#     ServiceSetBranding,
#     ServiceSmsSenderForm,
#     ServiceSwitchLettersForm,
#     SMSPrefixForm,
# )
from app.utils import (
    # AgreementInfo,
    # email_safe,
    # get_cdn_domain,
    user_has_permissions,
    # user_is_platform_admin,
)


@main.route("/services/<service_id>/service-settings/letters", methods=['GET'])
@login_required
@user_has_permissions('manage_service')
def service_settings_letters(service_id):
    letter_contact_details = service_api_client.get_letter_contacts(service_id)
    letter_contact_details_count = len(letter_contact_details)
    default_letter_contact_block = next(
        (Field(x['contact_block'], html='escape') for x in letter_contact_details if x['is_default']), "Not set"
    )

    return render_template(
        'views/service-settings/letters/index.html',
        default_letter_contact_block=default_letter_contact_block,
        letter_contact_details_count=letter_contact_details_count,
    )


@main.route("/services/<service_id>/service-settings/set-letters", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_set_letters(service_id):
    form = ServiceSwitchLettersForm(
        enabled='on' if 'letter' in current_service['permissions'] else 'off'
    )
    if form.validate_on_submit():
        force_service_permission(
            service_id,
            'letter',
            on=(form.enabled.data == 'on'),
        )
        return redirect(
            url_for(".service_settings", service_id=service_id)
        )
    return render_template(
        'views/service-settings/set-letters.html',
        form=form,
    )


@main.route("/services/<service_id>/service-settings/letter-contacts", methods=['GET'])
@login_required
@user_has_permissions('manage_service', 'manage_api_keys')
def service_letter_contact_details(service_id):
    letter_contact_details = service_api_client.get_letter_contacts(service_id)
    return render_template(
        'views/service-settings/letter-contact-details.html',
        letter_contact_details=letter_contact_details)


@main.route("/services/<service_id>/service-settings/letter-contact/add", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_add_letter_contact(service_id):
    form = ServiceLetterContactBlockForm()
    letter_contact_blocks_count = len(service_api_client.get_letter_contacts(service_id))
    first_contact_block = letter_contact_blocks_count == 0
    if form.validate_on_submit():
        service_api_client.add_letter_contact(
            current_service['id'],
            contact_block=form.letter_contact_block.data.replace('\r', '') or None,
            is_default=first_contact_block if first_contact_block else form.is_default.data
        )
        if request.args.get('from_template'):
            return redirect(
                url_for('.set_template_sender', service_id=service_id, template_id=request.args.get('from_template'))
            )
        return redirect(url_for('.service_letter_contact_details', service_id=service_id))
    return render_template(
        'views/service-settings/letter-contact/add.html',
        form=form,
        first_contact_block=first_contact_block)


@main.route("/services/<service_id>/service-settings/letter-contact/<letter_contact_id>/edit", methods=['GET', 'POST'])
@login_required
@user_has_permissions('manage_service')
def service_edit_letter_contact(service_id, letter_contact_id):
    letter_contact_block = service_api_client.get_letter_contact(service_id, letter_contact_id)
    form = ServiceLetterContactBlockForm(letter_contact_block=letter_contact_block['contact_block'])
    if request.method == 'GET':
        form.is_default.data = letter_contact_block['is_default']
    if form.validate_on_submit():
        service_api_client.update_letter_contact(
            current_service['id'],
            letter_contact_id=letter_contact_id,
            contact_block=form.letter_contact_block.data.replace('\r', '') or None,
            is_default=True if letter_contact_block['is_default'] else form.is_default.data
        )
        return redirect(url_for('.service_letter_contact_details', service_id=service_id))
    return render_template(
        'views/service-settings/letter-contact/edit.html',
        form=form,
        letter_contact_id=letter_contact_block['id'])
