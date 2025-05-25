# hiringgo-fe/authentication/forms.py
from django import forms

ROLE_CHOICES = [
    ('MAHASISWA', 'Mahasiswa'),
]

class RegistrationForm(forms.Form):
    namaLengkap = forms.CharField(label='Nama Lengkap', max_length=100,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email',
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirmPassword = forms.CharField(label='Konfirmasi Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(label='Daftar Sebagai', choices=ROLE_CHOICES,
                             widget=forms.Select(attrs={'class': 'form-control'}))
    nim = forms.CharField(label='NIM (Jika Mahasiswa)', max_length=20, required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    nip = forms.CharField(label='NIP (Jika Dosen)', max_length=30, required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmPassword")
        role = cleaned_data.get("role")
        nim = cleaned_data.get("nim")
        nip = cleaned_data.get("nip")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirmPassword', "Password dan konfirmasi password tidak cocok.")

        if role == 'MAHASISWA' and not nim:
            self.add_error('nim', "NIM tidak boleh kosong untuk mahasiswa.")
        elif role == 'DOSEN' and not nip:
            self.add_error('nip', "NIP tidak boleh kosong untuk dosen.")
        
        # Kosongkan field yang tidak relevan berdasarkan role agar tidak terkirim
        if role == 'MAHASISWA':
            cleaned_data['nip'] = None
        elif role == 'DOSEN':
            cleaned_data['nim'] = None

        return cleaned_data

class LoginForm(forms.Form):
    email = forms.EmailField(label='Email',
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))