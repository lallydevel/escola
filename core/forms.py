from django import forms
from .models import Aluno

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = '__all__'
        widgets = {
            'nome_aluno': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do aluno'}),
            'nome_mae': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da mãe'}),
            'contato': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Endereço completo'}),
            'turma': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 3º Ano B'}),
            'professor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do professor'}),
            'nota': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }