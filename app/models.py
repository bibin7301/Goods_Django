from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    def __str__(self):
            return self.name


class Home(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8 ,decimal_places=2)
    description = models.TextField()
    image = models.ImageField(
        upload_to='home/'
    )
    stock = models.PositiveBigIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self):
                return self.name
    