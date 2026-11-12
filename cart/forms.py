from django import forms


class AddToCartForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    override = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)

    def __init__(self, *args, max_quantity=None, **kwargs):
        super().__init__(*args, **kwargs)
        if max_quantity:
            self.fields["quantity"].max_value = max_quantity
            self.fields["quantity"].widget.attrs["max"] = max_quantity
