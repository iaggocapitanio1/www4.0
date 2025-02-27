from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from utilities.functions import generate_password
from utilities.links import get_activation_link, get_reset_password_link, get_portal_link

User = get_user_model()


def send_confirmation_email(request, user: User, template: str = "emailManager/confirmation.html"):
    subject = "Access Credentials for Mofreita Portal"
    link = get_portal_link()
    context = dict(username=user.username.__str__(), link=link,

                   msgBody=f"""Esperamos que esta mensagem o(a) encontre bem. Gostaríamos de fornecer a você os dados de
                    acesso necessários para o Portal Mofreita, a plataforma online que oferece uma ampla gama de 
                    recursos e informações relevantes. Por favor, mantenha essas informações em um local seguro e não 
                    compartilhe com terceiros.

                    Aqui estão os seus dados de acesso ao Portal Mofreita
                  """, password=generate_password(username=user.username))
    html_message = render_to_string(template_name=template, context=context)
    message = strip_tags(html_message)
    to = user.email
    from_email = settings.DEFAULT_FROM_EMAIL
    email = dict(subject=subject, message=message, from_email=from_email, recipient_list=[to],
                 fail_silently=False, html_message=html_message)

    return mail.send_mail(**email)


def send_confirmation_email_and_reset_password(request, user: User, template: str = "emailManager/confirmation.html"):
    subject = "Account Activation"
    # link = get_reset_password_link(request=request, user=user)
    link = get_portal_link()
    context = dict(username=user.username.__str__(), link=link,
                   msgBody=f"""Você está quase lá, clique no botão para ativar e resetar a password da sua conta e ser 
                   outro cliente da Mofreita.
                  """, password=generate_password(username=user.username), full_name=user.get_full_name())
    html_message = render_to_string(template_name=template, context=context)
    message = strip_tags(html_message)
    to = user.email
    from_email = settings.DEFAULT_FROM_EMAIL
    email = dict(subject=subject, message=message, from_email=from_email, recipient_list=[to],
                 fail_silently=False, html_message=html_message)

    return mail.send_mail(**email)


def has_nested_dicts(dictionary):
    for value in dictionary.values():
        if isinstance(value, dict):
            return True
    return False


def jsonld2json(fields: list, relational_fields: list, data: dict):
    new_data = dict()
    if has_nested_dicts(data):
        for key in fields:
            if data.get(key) is not None:
                new_data[key] = data[key]['value']
        for key in relational_fields:
            if data.get(key) is not None:
                new_data[key] = data[key]["object"]
    return new_data


def update_nested_data(fields: list, relational_fields: list, data: dict, old_data: dict) -> dict:
    if has_nested_dicts(dictionary=data):
        for field in fields:
            if (not data.get(field) or not data.get(field).get("value")) and old_data.get(field) is not None:
                data[field] = old_data[field]
        for field in relational_fields:
            if not data.get(field) or not data.get(field).get("object") and old_data.get(field) is not None:
                data[field] = old_data[field]
        data = jsonld2json(fields=fields, relational_fields=relational_fields, data=data)
    else:
        fields.extend(relational_fields)
        for field in fields:
            if not data[field] or not data[field] and old_data.get(field) is not None:
                data[field] = old_data[field]
    return data


def send_budget_changed(data, budget: dict, template: str = "emailManager/budgetChange.html"):
    from users.models import CustomerProfile
    from datetime import datetime
    fields = ["approvedDate", "name", "price"]
    relational_fields = ["approvedBy"]
    subject = "The budget has changed"

    data = update_nested_data(fields, relational_fields, data=data, old_data=budget)

    jsonData = dict(approvedDate=data["approvedDate"],
                    amount=data["price"],
                    name=data["name"])

    timestamp_str = jsonData['approvedDate']
    dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    jsonData.update(dict(approvedDate=dt.strftime('%d/%m/%Y')))

    orderBy = budget.get('orderBy', None)
    if orderBy:
        if orderBy.get('object'):
            customer_id: str = orderBy.get('object')
            customer_id = customer_id.split(':')[-1]
            customer: QuerySet = CustomerProfile.objects.filter(pk=customer_id)
        else:
            customer_id = orderBy.split(':')[-1]
            customer: QuerySet = CustomerProfile.objects.filter(pk=customer_id)
        if customer.exists():
            customer_obj = customer.first()
            context = dict(username=customer_obj.user.username, msgBody="O seu Orçamento foi alterado!",
                           jsonData=jsonData)
            html_message = render_to_string(template_name=template, context=context)
            message = strip_tags(html_message)
            to = customer_obj.user.email
            from_email = settings.DEFAULT_FROM_EMAIL
            email = dict(subject=subject, message=message, from_email=from_email, recipient_list=[to],
                         fail_silently=False,
                         html_message=html_message)
            return mail.send_mail(**email)


def send_reset_password_email(request, user: User, template: str = "emailManager/resetPassword.html"):
    subject = "Reset Password"
    context = dict(username=user.username.__str__(), link=get_reset_password_link(request=request, user=user),
                   msgBody="Clique no botão para alterar a senha. Se você não solicitou este serviço, ignore este "
                           "e-mail")
    html_message = render_to_string(template_name=template, context=context)
    message = strip_tags(html_message)
    to = user.email
    from_email = settings.DEFAULT_FROM_EMAIL
    email = dict(subject=subject, message=message, from_email=from_email, recipient_list=[to], fail_silently=False,
                 html_message=html_message)
    return mail.send_mail(**email)
