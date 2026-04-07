from django.shortcuts import render, redirect
from .forms import AlunoForm

def cadastrar_aluno(request):
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sucesso') # Redireciona após salvar
    else:
        form = AlunoForm()
    
    return render(request, 'core/cadastrar_aluno.html', {'form': form})

def home(request):
    return render(request, 'core/home.html')