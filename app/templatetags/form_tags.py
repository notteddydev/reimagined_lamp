from django import template

from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_control_class')
def add_control_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter(name='add_label_class')
def add_label_class(field, css_class):
    return field.label_tag(attrs={'class': css_class})

@register.filter(name='add_classes')
def add_classes(field, css_classes):
    """
    Adds classes to both the input and its label.
    The css_classes argument should be a string in the format 'input:class1 class2, label:class3 class4'.
    """
    input_class = ""
    label_class = ""
    
    classes = css_classes.split(",")
    for cls in classes:
        if 'input:' in cls:
            input_class = cls.split('input:')[1].strip()
        elif 'label:' in cls:
            label_class = cls.split('label:')[1].strip()
    
    field_widget = field.as_widget(attrs={'class': input_class})
    label = field.label_tag(attrs={'class': label_class})
    if label:
        return mark_safe(f"{label} {field_widget}")
    return mark_safe(field_widget)