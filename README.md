# StrideKicks 🏃‍♂️

**Premium Footwear E‑Commerce Platform**

*Step into style with every stride.*

---

StrideKicks is a Django- and Bootstrap-based e-commerce platform specifically designed for footwear retailers. It delivers a seamless shopping experience—browse, filter, cart, checkout—and provides a feature-rich admin dashboard for inventory, orders, promotions, and analytics.

[![Repo](https://img.shields.io/badge/repo-StrideKicks-181717?logo=github)](https://github.com/sooraj-m-s/StrideKicks)
![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-3.x%2B-092E20?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)
![Cloudinary](https://img.shields.io/badge/Cloudinary-Media-3448C5?logo=cloudinary&logoColor=white)

---

## Key Features

### Customer Experience
- **Product Catalog**: Browse by category, brand, and size.
- **Search & Filters**: Refine results by price, rating, and availability.
- **Cart & Wishlist**: Add products, save favorites, and review before purchase.
- **Secure Checkout**: Multiple payment gateways, shipping address management.

### Admin Dashboard
- **Product & Inventory**: Add, edit, and organize shoe listings.
- **Brand & Category**: Manage brand profiles and category hierarchies.
- **Order Processing**: View, update, and fulfill orders.
- **User Management**: Role-based access and profile administration.
- **Promotions**: Create and manage discounts, coupon code management.
- **Analytics**: Sales charts, revenue reports, and performance metrics.

---

## Technology Stack

| Layer      | Technologies              |
|-----------:|---------------------------|
| Backend    | Python 3.x, Django        |
| Database   | PostgreSQL                |
| Frontend   | HTML5, CSS3, JavaScript   |
| UI Library | Bootstrap 5, Font Awesome |

---

## Getting Started

1. **Clone repository**
   ```bash
   git clone https://github.com/sooraj-m-s/StrideKicks.git
   cd StrideKicks


2. **Set up environment**
   ```bash
   python3 -m venv env_stridekicks
   source env_stridekicks/bin/activate  # Windows: env_stridekicks\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Database migration**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server**
   ```bash
   python manage.py runserver
   ```

6. **Access application**
   - Frontend: [http://localhost:8000/](http://localhost:8000/)
   - Admin: [http://localhost:8000/admin/login/](http://localhost:8000/admin/login/)

---

## Contributing

Contributions are welcome. To propose changes:

1. Fork the repository.
2. Create a branch: `git checkout -b feature/YourFeature`.
3. Commit changes: `git commit -m "Add YourFeature"`.
4. Push branch: `git push origin feature/YourFeature`.
5. Open a Pull Request.

Please ensure your code follows our coding standards and includes appropriate tests.

---


## 📞 Contact

For questions or feedback, reach out to **[soorajms4@gmail.com](mailto:soorajms4@gmail.com)**.