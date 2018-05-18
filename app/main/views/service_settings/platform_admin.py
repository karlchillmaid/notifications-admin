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
    # user_has_permissions,
    user_is_platform_admin,
)


@main.route("/services/<service_id>/service-settings/can-send-email")
@login_required
@user_is_platform_admin
def service_switch_can_send_email(service_id):
    switch_service_permissions(service_id, 'email')
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<service_id>/service-settings/can-send-sms")
@login_required
@user_is_platform_admin
def service_switch_can_send_sms(service_id):
    switch_service_permissions(service_id, 'sms')
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<service_id>/service-settings/email-auth")
@login_required
@user_is_platform_admin
def service_switch_email_auth(service_id):
    switch_service_permissions(service_id, 'email_auth')
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<service_id>/service-settings/can-send-precompiled-letter")
@login_required
@user_is_platform_admin
def service_switch_can_send_precompiled_letter(service_id):
    switch_service_permissions(service_id, 'precompiled_letter')
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<service_id>/service-settings/can-upload-document")
@login_required
@user_is_platform_admin
def service_switch_can_upload_document(service_id):
    switch_service_permissions(service_id, 'upload_document')
    return redirect(url_for('.service_settings', service_id=service_id))


@main.route("/services/<service_id>/service-settings/set-organisation-type", methods=['GET', 'POST'])
@login_required
@user_is_platform_admin
def set_organisation_type(service_id):

    form = OrganisationTypeForm(organisation_type=current_service.get('organisation_type'))

    if form.validate_on_submit():
        free_sms_fragment_limit = current_app.config['DEFAULT_FREE_SMS_FRAGMENT_LIMITS'].get(
            form.organisation_type.data)

        service_api_client.update_service(
            service_id,
            organisation_type=form.organisation_type.data,
        )
        billing_api_client.create_or_update_free_sms_fragment_limit(service_id, free_sms_fragment_limit)

        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-organisation-type.html',
        form=form,
    )


@main.route("/services/<service_id>/service-settings/set-free-sms-allowance", methods=['GET', 'POST'])
@login_required
@user_is_platform_admin
def set_free_sms_allowance(service_id):

    form = FreeSMSAllowance(free_sms_allowance=billing_api_client.get_free_sms_fragment_limit_for_year(service_id))

    if form.validate_on_submit():
        billing_api_client.create_or_update_free_sms_fragment_limit(service_id, form.free_sms_allowance.data)

        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/set-free-sms-allowance.html',
        form=form,
    )


@main.route("/services/<service_id>/service-settings/set-email-branding", methods=['GET', 'POST'])
@login_required
@user_is_platform_admin
def service_set_email_branding(service_id):
    email_branding = email_branding_client.get_all_email_branding()

    form = ServiceSetBranding(branding_type=current_service.get('branding'))

    # dynamically create org choices, including the null option
    form.branding_style.choices = [('None', 'None')] + get_branding_as_value_and_label(email_branding)

    if form.validate_on_submit():
        branding_style = None if form.branding_style.data == 'None' else form.branding_style.data
        service_api_client.update_service(
            service_id,
            branding=form.branding_type.data,
            email_branding=branding_style
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    form.branding_style.data = current_service['email_branding'] or 'None'

    return render_template(
        'views/service-settings/set-email-branding.html',
        form=form,
        branding_dict=get_branding_as_dict(email_branding)
    )


@main.route("/services/<service_id>/service-settings/set-letter-branding", methods=['GET', 'POST'])
@login_required
@user_is_platform_admin
def set_letter_branding(service_id):

    form = LetterBranding(choices=email_branding_client.get_letter_email_branding().items())

    if form.validate_on_submit():
        service_api_client.update_service(
            service_id,
            dvla_organisation=form.dvla_org_id.data
        )
        return redirect(url_for('.service_settings', service_id=service_id))

    form.dvla_org_id.data = current_service.get('dvla_organisation', '001')

    return render_template(
        'views/service-settings/set-letter-branding.html',
        form=form,
    )


@main.route("/services/<service_id>/service-settings/link-service-to-organisation", methods=['GET', 'POST'])
@login_required
@user_is_platform_admin
def link_service_to_organisation(service_id):

    organisations = organisations_client.get_organisations()
    current_organisation = organisations_client.get_service_organisation(service_id).get('id', None)

    form = LinkOrganisationsForm(
        choices=convert_dictionary_to_wtforms_choices_format(organisations, 'id', 'name'),
        organisations=current_organisation
    )

    if form.validate_on_submit():
        if form.organisations.data != current_organisation:
            organisations_client.update_service_organisation(
                service_id,
                form.organisations.data
            )
        return redirect(url_for('.service_settings', service_id=service_id))

    return render_template(
        'views/service-settings/link-service-to-organisation.html',
        has_organisations=organisations,
        form=form,
    )


def get_branding_as_value_and_label(email_branding):
    return [
        (branding['id'], branding['name'])
        for branding in email_branding
    ]


def get_branding_as_dict(email_branding):
    return {
        branding['id']: {
            'logo': 'https://{}/{}'.format(get_cdn_domain(), branding['logo']),
            'colour': branding['colour']
        } for branding in email_branding
    }


def convert_dictionary_to_wtforms_choices_format(dictionary, value, label):
    return [
        (item[value], item[label]) for item in dictionary
    ]
