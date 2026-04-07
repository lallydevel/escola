from django.db import models

class Aluno(models.Model):
    nome_aluno = models.CharField(max_length=100)
    nome_mae = models.CharField(max_length=100)
    contato = models.CharField(max_length=20)
    email = models.EmailField()
    endereco = models.CharField(max_length=255)
    turma = models.CharField(max_length=50)
    professor = models.CharField(max_length=100)
    nota = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nome_aluno