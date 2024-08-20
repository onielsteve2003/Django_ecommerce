from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.core import mail
from ..models import CustomUser, Product, Category
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile
from store.serializers import ProductSerializer
from PIL import Image
from io import BytesIO

User = get_user_model()

class SignupViewTests(APITestCase):
    
    def setUp(self):
        self.signup_url = '/api/auth/signup/'
        self.valid_payload = {
            'name': 'John Doe',
            'email': 'johndoe@example.com',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'address': '123 Elm Street',
            'phone_number': '+1234567890'
        }

    def test_signup_success(self):
        response = self.client.post(self.signup_url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], "Successful signup. Thank you for signing up to Stephen's Stores.")
        self.assertTrue(response.data['success'])

        # Verify that the user was created
        user_exists = CustomUser.objects.filter(email=self.valid_payload['email']).exists()
        self.assertTrue(user_exists)

    def test_email_sent(self):
        # Send the request
        response = self.client.post(self.signup_url, self.valid_payload, format='json')

        # Verify the email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Thank You for Signing Up')
        self.assertIn("Thank you for signing up to Stephen's Stores", email.body)
        self.assertEqual(email.to, [self.valid_payload['email']])

    def test_signup_missing_field(self):
        invalid_payload = self.valid_payload.copy()
        del invalid_payload['email']
        response = self.client.post(self.signup_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_signup_password_mismatch(self):
        invalid_payload = self.valid_payload.copy()
        invalid_payload['confirm_password'] = 'differentpassword'
        response = self.client.post(self.signup_url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('confirm_password', response.data)

class LoginViewTests(APITestCase):
    
    def setUp(self):
        self.login_url = '/api/auth/login/'
        self.user_data = {
            'email': 'johndoe@example.com',
            'password': 'securepassword123'
        }
        self.user = get_user_model().objects.create_user(
            email=self.user_data['email'],
            password=self.user_data['password'],
            name='John Doe',
            address='123 Elm Street',
            phone_number='+1234567890'
        )

    def test_login_success(self):
        response = self.client.post(self.login_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], "Login successful")
        self.assertTrue(response.data['success'])
        self.assertIn('token', response.data)
        self.assertEqual(response.data['userId'], self.user.id)

    def test_login_invalid_credentials(self):
        invalid_user_data = {
            'email': 'wrongemail@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, invalid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['message'], "Invalid email or password")
        self.assertFalse(response.data['success'])

    def test_login_missing_field(self):
        response = self.client.post(self.login_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['message'], "Email and password are required")
        self.assertFalse(response.data['success'])

class ProfileTests(APITestCase):
    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword123',
            name='Test User',
            address='123 Test Address',
            phone_number='+1234567890'
        )
        # Generate a token for authentication
        self.token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_profile(self):
        """Test that the profile can be retrieved successfully."""
        response = self.client.get('/api/auth/profile/')
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Successfully fetched profile')
        self.assertEqual(response.data['data']['name'], self.user.name)
        self.assertEqual(response.data['data']['email'], self.user.email)
        self.assertEqual(response.data['data']['address'], self.user.address)
        self.assertEqual(response.data['data']['phone_number'], self.user.phone_number)
        self.assertTrue(response.data['success'])

    def test_update_profile(self):
        """Test that the profile can be updated successfully."""
        data = {
            'name': 'Updated Name',
            'address': '456 Updated Address',
            'phone_number': '+0987654321'
        }
        response = self.client.put('/api/auth/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Successfully updated user')
        self.assertEqual(response.data['data']['name'], 'Updated Name')
        self.assertEqual(response.data['data']['address'], '456 Updated Address')
        self.assertEqual(response.data['data']['phone_number'], '+0987654321')
        self.assertTrue(response.data['success'])

    def test_update_profile_unauthorized(self):
        """Test that the profile cannot be updated if not authenticated."""
        self.client.credentials()  # Remove token
        data = {
            'name': 'Unauthorized Update',
            'address': '999 Unauthorized Address',
            'phone_number': '+0000000000'
        }
        response = self.client.put('/api/auth/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 401)
        self.assertEqual(response.data['message'], 'Authentication credentials were not provided or are invalid')
        self.assertFalse(response.data['success'])

class ProductTests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

        # Create categories
        category1 = Category.objects.create(
            name='Category 1',
            description='Description for Category 1',
            created_by=self.user
        )
        category2 = Category.objects.create(
            name='Category 2',
            description='Description for Category 2',
            created_by=self.user
        )

        # Create some test products
        Product.objects.create(
            name='Product 1',
            description='Description 1',
            price=10.00,
            stock_quantity=100,
            category=category1,
            image='path/to/image1.jpg',
            created_by=self.user
        )
        Product.objects.create(
            name='Product 2',
            description='Description 2',
            price=20.00,
            stock_quantity=50,
            category=category2,
            image='path/to/image2.jpg',
            created_by=self.user
        )

    def test_list_products(self):
        url = '/api/products'
        response = self.client.get(url, follow=True)
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the response data
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Successfully retrieved all products')
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], dict)
        self.assertIn('products', response.data['data'])
        self.assertIsInstance(response.data['data']['products'], list)

    def test_list_products_with_filters(self):
        url = '/api/products?category=Category 1'
        response = self.client.get(url, follow=True)
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the response data
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Successfully retrieved all products')
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], dict)
        self.assertIn('products', response.data['data'])
        self.assertIsInstance(response.data['data']['products'], list)
        self.assertEqual(len(response.data['data']['products']), 1)  # Only one product in 'Category 1'
        self.assertEqual(response.data['data']['products'][0]['name'], 'Product 1')
        
    def test_list_products_with_pagination(self):
        url = '/api/products?page=1&page_size=1'
        response = self.client.get(url, follow=True)
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check the response data
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Successfully retrieved all products')
        self.assertTrue(response.data['success'])
        self.assertIsInstance(response.data['data'], dict)
        self.assertIn('products', response.data['data'])
        self.assertIsInstance(response.data['data']['products'], list)
        self.assertEqual(len(response.data['data']['products']), 1)  # Pagination should limit to 1 product

        # Check pagination links
        next_link = response.data['data'].get('next')
        previous_link = response.data['data'].get('previous')

        # Verify the presence of the 'next' link
        if next_link:
            self.assertIsInstance(next_link, str)
        else:
            self.assertIsNone(next_link)
        
        # Verify the 'previous' link (should be None for the first page)
        self.assertIsNone(previous_link)

class ProductCreateViewTests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)  # Authenticate the user

        # Create a test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user
        )

        self.url = reverse('product-create')  # Ensure this URL matches your URLconf

    def create_image(self):
        # Create an image file for testing
        image_file = BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(image_file, format='JPEG')
        image_file.seek(0)
        return SimpleUploadedFile(name='test_image.jpg', content=image_file.read(), content_type='image/jpeg')

    def test_create_product_success(self):
        image = self.create_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 10.99,
            'stock_quantity': 50,
            'category': self.category.id,  # Use category ID
            'image': image,
        }
        response = self.client.post(self.url, data, format='multipart')
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['code'], 201)
        self.assertEqual(response.data['message'], 'Product successfully created')
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Test Product')
        self.assertEqual(response.data['data']['description'], 'Test Description')
        self.assertEqual(float(response.data['data']['price']), 10.99)  # Ensure price is correctly formatted
        self.assertEqual(response.data['data']['stock_quantity'], 50)
        self.assertEqual(response.data['data']['category'], self.category.id)

    def test_create_product_invalid_price(self):
        image = self.create_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': -10.99,
            'stock_quantity': 50,
            'category': self.category.id,  # Use category ID
            'image': image
        }
        response = self.client.post(self.url, data, format='multipart')
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertEqual(response.data['price'][0], 'Price must be greater than zero.')

    def test_create_product_invalid_stock_quantity(self):
        image = self.create_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 10.99,
            'stock_quantity': -5,
            'category': self.category.id,  # Use category ID
            'image': image
        }
        response = self.client.post(self.url, data, format='multipart')
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('stock_quantity', response.data)
        self.assertEqual(response.data['stock_quantity'][0], 'Ensure this value is greater than or equal to 0.')

    def test_create_product_missing_image(self):
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 10.99,
            'stock_quantity': 50,
            'category': self.category.id  # Use category ID
        }
        response = self.client.post(self.url, data, format='multipart')
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('image', response.data)
        self.assertEqual(response.data['image'][0], 'No file was submitted.')

    def test_create_product_unauthorized(self):
        self.client.logout()  # Log out the user
        image = self.create_image()
        data = {
            'name': 'Test Product',
            'description': 'Test Description',
            'price': 10.99,
            'stock_quantity': 50,
            'category': self.category.id,  # Use category ID
            'image': image
        }
        response = self.client.post(self.url, data, format='multipart')
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 401)
        self.assertEqual(response.data['message'], 'Authentication credentials were not provided or are invalid')
        self.assertFalse(response.data['success'])

class ProductDetailViewTests(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)

        # Create a test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user
        )

        # Create a product associated with the test category
        self.product = Product.objects.create(
            name='Test Product',
            description='Test Description',
            price=10.99,
            stock_quantity=50,
            category=self.category,  # Use the Category instance
            image=None,
            created_by=self.user
        )
        self.url = reverse('product-detail', kwargs={'pk': self.product.pk})

    def test_retrieve_product_success(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Successfully retrieved single product')
        self.assertTrue(response.data['success'])
        
        # Create a serializer instance and compare the data
        serializer = ProductSerializer(self.product)
        self.assertEqual(response.data['data'], serializer.data)

    def test_retrieve_product_not_found(self):
        non_existent_url = reverse('product-detail', kwargs={'pk': 999})
        response = self.client.get(non_existent_url)
        
        # Check the response status code
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Validate the error response format
        self.assertIn('code', response.data)
        self.assertEqual(response.data.get('code'), 404)
        self.assertIn('message', response.data)
        self.assertEqual(response.data.get('message'), 'No Product matches the given query.')
        self.assertIn('success', response.data)
        self.assertFalse(response.data.get('success'))

class ProductUpdateViewTests(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword'
        )
        
        # Generate a JWT token for the user
        self.token = self._get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Create a test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user
        )

        # Create a product owned by the user
        self.product = Product.objects.create(
            name='Test Product',
            description='A description of the test product',
            price=10.00,
            stock_quantity=100,
            category=self.category,
            image=None,  # Use None for simplicity in this test
            created_by=self.user
        )
        self.update_url = reverse('product-update', kwargs={'pk': self.product.id})

    def _get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_successful_update(self):
        update_data = {
            'name': 'Updated Product Name',
            'description': 'Updated description',
            'price': 15.00,
            'stock_quantity': 200,
            'category': self.category.id
        }
        response = self.client.patch(self.update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Product successfully updated')
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['name'], 'Updated Product Name')
        self.assertEqual(response.data['data']['description'], 'Updated description')

        # Verify the product was updated in the database
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Product Name')
        self.assertEqual(self.product.description, 'Updated description')
        self.assertEqual(self.product.price, 15.00)
        self.assertEqual(self.product.stock_quantity, 200)

    def test_product_not_found(self):
        invalid_url = reverse('product-update', kwargs={'pk': 9999})  # An ID that doesn't exist
        response = self.client.patch(invalid_url, {'name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['code'], 404)
        self.assertEqual(response.data['message'], 'Product not found')
        self.assertFalse(response.data['success'])

    def test_permission_denied(self):
        # Create another user who does not own the product
        another_user = User.objects.create_user(
            email='anotheruser@example.com',
            password='anotherpassword'
        )
        # Use a token for the new user
        token = self._get_jwt_token(another_user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

        response = self.client.patch(self.update_url, {'name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['code'], 403)
        self.assertEqual(response.data['message'], 'You do not have permission to edit this product.')
        self.assertFalse(response.data['success'])

    def test_invalid_data(self):
        # Providing invalid data
        update_data = {
            'price': -10.00,  # Invalid price
            'stock_quantity': -5  # Invalid stock quantity
        }
        response = self.client.patch(self.update_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
        self.assertEqual(response.data['message'], 'Invalid data')
        self.assertFalse(response.data['success'])

        # Check if specific errors are included in the response
        data_errors = response.data.get('data', {})
        self.assertIn('stock_quantity', data_errors)
        self.assertNotIn('price', data_errors)

        # Check if error details contain 'min_value'
        stock_quantity_errors = data_errors.get('stock_quantity', [])
        self.assertTrue(any(error.code == 'min_value' for error in stock_quantity_errors))

class ProductDeleteViewTest(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpassword'
        )
        
        # Generate a JWT token for the user
        self.token = self._get_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        # Create a test category
        self.category = Category.objects.create(
            name='Test Category',
            created_by=self.user
        )

        # Create a product owned by the user
        self.product = Product.objects.create(
            name='Test Product',
            description='A description of the test product',
            price=10.00,
            stock_quantity=100,
            category=self.category,
            image=None,  # Use None for simplicity in this test
            created_by=self.user
        )
        self.delete_url = reverse('product-delete', kwargs={'id': self.product.id})

    def _get_jwt_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_successful_deletion(self):
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'code': 200,
            'message': 'Product successfully deleted',
            'data': {},
            'success': True
        })
        # Verify that the product has been deleted
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_product_not_found(self):
        invalid_url = reverse('product-delete', kwargs={'id': 9999})  # An ID that doesn't exist
        response = self.client.delete(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            'code': 404,
            'message': "Product not found or you don't have permission to delete it.",
            'data': {},
            'success': False
        })

    def test_permission_denied(self):
        # Create another user who does not have permission to delete this product
        another_user = User.objects.create_user(
            email='anotheruser@example.com',
            password='anotherpassword'
        )
        # Use a token for the new user
        token = self._get_jwt_token(another_user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)

        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            'code': 404,
            'message': "Product not found or you don't have permission to delete it.",
            'data': {},
            'success': False
        })

class CategoryListTestCase(APITestCase):

    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(email='testuser@example.com', password='password123')

        # Create some sample categories
        self.category1 = Category.objects.create(
            name="Electronics",
            description="All kinds of electronic items.",
            created_by=self.user  # Associate with the created user
        )
        self.category2 = Category.objects.create(
            name="Books",
            description="A wide range of books and literature.",
            created_by=self.user  # Associate with the created user
        )

        # Authenticate the user
        self.client.login(email='testuser@example.com', password='password123')

    def test_list_categories(self):
        # Define the endpoint
        url = reverse('category-list')
        
        # Send a GET request to the endpoint
        response = self.client.get(url)
        
        # Assert the status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Assert the structure of the response
        self.assertIn('code', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('success', response.data)
        
        # Assert the content of the response
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], "Categories retrieved successfully")
        self.assertTrue(response.data['success'])
        
        # Assert the data content
        self.assertIn('categories', response.data['data'])
        self.assertEqual(len(response.data['data']['categories']), 2)  # 2 categories created in setUp
        self.assertEqual(response.data['data']['categories'][0]['name'], "Electronics")
        self.assertEqual(response.data['data']['categories'][1]['name'], "Books")

class CategoryCreateTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='password123')
        self.url = reverse('category-add')

        # Obtain a JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_create_category_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)  # Set the Authorization header
        data = {
            'name': 'Fashion',
            'description': 'Clothing and accessories'
        }

        response = self.client.post(self.url, data)

        # Assert the status code
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert the response structure
        self.assertIn('code', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('success', response.data)

        # Assert the content of the response
        self.assertEqual(response.data['code'], 201)
        self.assertEqual(response.data['message'], "Category created successfully")
        self.assertTrue(response.data['success'])

        # Assert the category was created
        self.assertTrue(Category.objects.filter(name='Fashion').exists())

    def test_create_category_unauthenticated(self):
        data = {
            'name': 'Fashion',
            'description': 'Clothing and accessories'
        }
        
        response = self.client.post(self.url, data)
        
        # Print the response for debugging
        # print(response.data)
        
        # Assert the status code
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Assert the response structure
        self.assertIn('code', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('success', response.data)

        # Assert the content of the response
        self.assertEqual(response.data['code'], 401)
        
        # Handle potential variations in the error message
        self.assertIn("Authentication credentials were not provided", response.data['message'])
        self.assertFalse(response.data['success'])

class CategoryUpdateViewTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='password123')
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))

        self.category = Category.objects.create(
            name='Fashion',
            description='Clothing and accessories',
            created_by=self.user
        )
        self.url = reverse('category-update', args=[self.category.id])

    def test_update_category_authenticated(self):
        data = {
            'name': 'Updated Fashion',
            'description': 'Updated description'
        }
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Fashion')
        self.assertEqual(self.category.description, 'Updated description')

    def test_update_category_unauthorized(self):
        self.client.credentials()  # Logout
        data = {
            'name': 'Unauthorized Update',
            'description': 'This should fail'
        }
        response = self.client.put(self.url, data, format='json')
        # print(f"Unauthorized Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 401)
        self.assertIn('Authentication credentials were not provided', response.data['message'])
        self.assertFalse(response.data['success'])

    def test_update_category_with_invalid_data(self):
        data = {
            'name': ''  # Empty name should be invalid
        }
        response = self.client.put(self.url, data, format='json')
        # print(f"Invalid Data Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['code'], 400)
        self.assertIn('name', response.data['data'])
        self.assertFalse(response.data['success'])

    def test_update_non_existing_category(self):
        non_existing_url = reverse('category-update', args=[999])  # Use an ID that does not exist
        data = {
            'name': 'Non-existing Category'
        }
        response = self.client.put(non_existing_url, data, format='json')
        # print(f"Non-existing Category Response: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['code'], 404)
        self.assertIn('Category not found or you do not have permission to update it', response.data['message'])
        self.assertFalse(response.data['success'])

class CategoryDeleteTestCase(APITestCase):

    def setUp(self):
        # Create a user and authenticate them
        self.user = User.objects.create_user(email='testuser@example.com', password='password123')
        self.client.force_authenticate(user=self.user)

        # Create a category
        self.category = Category.objects.create(name='Test Category', description='A test category', created_by=self.user)

        # Create another user and category
        self.other_user = User.objects.create_user(email='otheruser@example.com', password='password123')
        self.other_category = Category.objects.create(name='Other Category', description='Another test category', created_by=self.other_user)

    def test_delete_category_authenticated(self):
        url = reverse('category-delete', args=[self.category.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], 'Category deleted successfully')
        self.assertTrue(response.data['success'])

        # Verify that the category is actually deleted
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    def test_delete_category_unauthenticated(self):
        self.client.logout()
        url = reverse('category-delete', args=[self.category.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 401)
        self.assertEqual(response.data['message'], 'Authentication credentials were not provided or are invalid')
        self.assertFalse(response.data['success'])

    def test_delete_category_not_owner(self):
        url = reverse('category-delete', args=[self.other_category.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['code'], 404)
        self.assertEqual(response.data['message'], 'Category not found or you do not have permission to delete it')
        self.assertFalse(response.data['success'])

        # Verify that the other user's category is not deleted
        self.assertTrue(Category.objects.filter(id=self.other_category.id).exists())

