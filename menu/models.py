from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Food(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="foods"
    )

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    reward_points = models.IntegerField(default=0, help_text="Points earned when customer orders this item")

    image = models.ImageField(
        upload_to="foods/",
        blank=True,
        null=True
    )

    available = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False, help_text="Mark as popular to show on homepage")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name