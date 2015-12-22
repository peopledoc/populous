from django.db import models
from django.contrib.auth.models import User

ABODE_TYPES = (
    ('SH', 'Small house'),
    ('H',  'House'),
    ('SB', 'Small building'),
    ('B',  'Building')
)

GENDERS = (
    ('M', 'Male'),
    ('F', 'Female')
)


class World(models.Model):
    god = models.ForeignKey(User, related_name='worlds')

    name = models.CharField(max_length=30)
    description = models.TextField()


class City(models.Model):
    world = models.ForeignKey(World, related_name='cities')

    name = models.CharField(max_length=40)


class Abode(models.Model):
    city = models.ForeignKey(City, related_name='abodes')
    owner = models.OneToOneField('Citizen', related_name='owned_house')

    type = models.CharField(max_length=2, choices=ABODE_TYPES)


class Citizen(models.Model):
    abode = models.ForeignKey(Abode, related_name='citizens')

    first_name = models.CharField(max_length=20)
    middle_name = models.CharField(max_length=20, blank=True, default='')
    last_name = models.CharField(max_length=20)
    birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDERS)


class Hobby(models.Model):
    name = models.CharField(max_length=40)
    citizens = models.ManyToManyField(Citizen)
