import copy
from datetime import date

from django.db.utils import IntegrityError
from django.test import TestCase

from rolepermissions.verifications import has_role

from orders_manager.models import UserProfile, Client, ClientChild, \
    AdditionalService, Order, Program, ProgramPrice, Discount

from orders_manager.utils.generate_data_helper import UserProfileGenerator, \
    ProgramGenerator, AdditionalServicesGenerator


class UserRolesTestCase(TestCase):
    #####################################
    # Creating users with roles
    #####################################

    user_info = {
        'username': 'john_trivolta',
        'first_name': 'John',
        'last_name': 'Trivolta',
        'email': 'john@trivolta.com',
        'phone': '+375(29)218-63-45',
        'password': 'some_password',
        'address': 'Minsk, st.SomeStreet',
    }

    def setUp(self):
        us_gen = UserProfileGenerator()
        us_gen.generate(role=UserProfileGenerator.ANIMATOR, num=5)
        us_gen.generate(role=UserProfileGenerator.MANAGER, num=3)
        us_gen.generate(role=UserProfileGenerator.PHOTOGRAPHER, num=1)

    def test_create_animator(self):
        UserProfile.objects.create_animator(**self.user_info)
        animator = UserProfile.objects.filter(
            user__username=self.user_info['username']).first()
        self.assertEqual(self.user_info.get('username'),
                         animator.get_username())
        self.assertEqual(self.user_info.get('first_name'),
                         animator.get_first_name())
        self.assertEqual(self.user_info.get('last_name'),
                         animator.get_last_name())
        self.assertEqual(self.user_info.get('email'), animator.get_email())
        self.assertEqual(self.user_info.get('phone'), animator.get_phone())
        self.assertEqual(self.user_info.get('address'), animator.get_address())
        self.assertTrue(has_role(animator.user, UserProfileGenerator.ANIMATOR))

    def test_create_photographer(self):
        UserProfile.objects.create_photographer(**self.user_info)
        manager = UserProfile.objects.filter(
            user__username=self.user_info['username']).first()
        self.assertTrue(
            has_role(manager.user, UserProfileGenerator.PHOTOGRAPHER))

    def test_create_manager(self):
        UserProfile.objects.create_manager(**self.user_info)
        manager = UserProfile.objects.filter(
            user__username=self.user_info['username']).first()
        self.assertTrue(has_role(manager.user, UserProfileGenerator.MANAGER))

    #####################################
    # Search users by roles
    #####################################

    def test_get_all_animators(self):
        animators = UserProfile.objects.all_animators()
        self.assertEqual(5, len(animators))

    def test_get_all_managers(self):
        managers = UserProfile.objects.all_managers()
        self.assertEqual(3, len(managers))

    def test_get_all_photographer(self):
        photographers = UserProfile.objects.all_photographers()
        self.assertEqual(1, len(photographers))

    def test_get_all_executors(self):
        executors = UserProfile.objects.all_executors()
        self.assertEqual(6, len(executors))

        #####################################
        # Getting program bonus for user
        #####################################

        # def test_get_user_bonus(self):
        #     user = UserProfile.objects.get(user_id=6)
        #     bonus = user.get_bonus_for_program(program_id=1)
        #     self.assertEqual(30, bonus)
        #     self.assertNotEqual(32, bonus)
        #     bonus = user.get_bonus_for_program(program_id=2)
        #     self.assertEqual(46, bonus)
        #     self.assertNotEqual(30, bonus)
        #     bonus = user.get_bonus_for_program(program_id=3)
        #     self.assertEqual(64, bonus)
        #     self.assertNotEqual(30, bonus)
        #     bonus = user.get_bonus_for_program(program_id=4)
        #     self.assertEqual(16, bonus)
        #     self.assertNotEqual(30, bonus)
        #     user = UserProfile.objects.get(user_id=2)
        #
        #     # Manager get 0
        #     bonus = user.get_bonus_for_program(program_id=1)
        #     self.assertEqual(0, bonus)
        #     self.assertNotEqual(32, bonus)


# ==============================================================================

class ClientTestCase(TestCase):
    client_info = {
        'name': 'some_client',
        'phone': '123-235-456',
        'phone_2': '',
        'email': 'john@trivolta.com',
        'vk_link': 'some_password',
        'odnoklassniki_link': 'odnoklassniki_link',
        'instagram_link': 'instagram_link',
        'facebook_link': 'facebook_link',
        'secondby_link': 'secondby_link',
        'comments': 'some comment',
    }

    children_info = {
        'name': 'Сергей',
        'birthday': '2008-03-10'
    }

    def test_create_client_common_case(self):
        client = Client.objects.create(**self.client_info)
        self.assertEqual(self.client_info.get('name'), client.name)

    def test_create_client_unique_phone(self):
        client = Client.objects.create(**self.client_info)
        self.assertEqual(self.client_info.get('name'), client.name)

        self.client_info['name'] = 'Вано'

        with self.assertRaises(IntegrityError):
            Client.objects.create(**self.client_info)

    def test_create_client_phone_required(self):
        self.client_info['phone'] = None

        with self.assertRaises(IntegrityError):
            Client.objects.create(**self.client_info)

        self.client_info['phone'] = '+375(29)219-46-15'

    def test_update_or_create_client(self):
        Client.objects.update_or_create(**self.client_info)
        self.client_info['name'] = 'Толик'
        Client.objects.update_or_create(**self.client_info)
        self.assertEqual(1, len(Client.objects.all()))
        client = Client.objects.first()
        self.assertEqual('Толик', client.name)

    def test_create_client_children(self):
        client = Client.objects.create(**{
            'name': 'Джон Тривольта',
            'phone': '+375(29)594-46-73'
        })
        ClientChild.objects.create(**{
            'name': 'Васёк',
            'client_id': client.id,
            'age': '4',
            'celebrate_date': 'Дата: 17.10.2015   Время: 10:20'
        })
        client_children = client.children.all()
        self.assertEqual(1, len(client_children))
        self.assertEqual('Васёк', client_children[0].name)

    def test_create_children_unique_name_for_parent(self):
        client = Client.objects.create(**{
            'name': 'Джон Тривольта',
            'phone': '+375(29)594-46-73'
        })
        ClientChild.objects.create(**{
            'name': 'Васёк',
            'client_id': client.id,
            'age': '4',
            'celebrate_date': 'Дата: 17.10.2015   Время: 10:20'
        })
        with self.assertRaises(IntegrityError):
            ClientChild.objects.create(**{
                'name': 'Васёк',
                'client_id': client.id,
                'age': '5',
                'celebrate_date': 'Дата: 02.02.2016   Время: 10:28'
            })

    def test_create_children_has_same_names_for_different_parents(self):
        client_1 = Client.objects.create(**{
            'name': 'Джон Тривольта',
            'phone': '+375(29)594-46-73'
        })
        ClientChild.objects.create(**{
            'name': 'Васёк',
            'client_id': client_1.id,
            'age': '4',
            'celebrate_date': 'Дата: 17.10.2015   Время: 10:20'
        })
        client_2 = Client.objects.create(**{
            'name': 'John Doe',
            'phone': '+375(29)698-42-78'
        })
        ClientChild.objects.create(**{
            'name': 'Васёк',
            'client_id': client_2.id,
            'age': '8',
            'celebrate_date': 'Дата: 17.10.2015   Время: 10:20'
        })
        self.assertEqual(1, len(client_1.children.all()))
        self.assertEqual(1, len(client_2.children.all()))

    def test_create_client_children_calculate_birthday(self):
        client = Client.objects.create(**{
            'name': 'Джон Тривольта',
            'phone': '+375(29)594-46-73'
        })
        ClientChild.objects.create(**{
            'name': 'Васёк',
            'client_id': client.id,
            'age': '4',
            'celebrate_date': 'Дата: 17.10.2015   Время: 10:20'
        })
        self.assertEqual(date(2010, 10, 17), client.children.get(
            name='Васёк').birthday)
        self.assertNotEqual(date(2010, 10, 16), client.children.get(
            name='Васёк').birthday)
        client.children.add(ClientChild.objects.create(**{
            'name': 'Петруха',
            'client_id': client.id,
            'age': '8',
            'celebrate_date': '2015-12-08'
        }))
        self.assertEqual(date(2006, 12, 8), client.children.get(
            name='Петруха').birthday)
        self.assertNotEqual(date(2006, 12, 9), client.children.get(
            name='Петруха').birthday)
        self.assertEqual(2, len(client.children.all()))

    def test_update_or_create_child(self):
        client = Client.objects.create(**self.client_info)
        ClientChild.objects.update_or_create(**{
            'name': 'Картменез',
            'client_id': client.id,
            'age': '8',
            'celebrate_date': '2015-11-24'
        })
        ClientChild.objects.update_or_create(**{
            'name': 'Стэн',
            'client_id': client.id,
            'birthday': '2006-11-01'
        })
        self.assertEqual(date(2006, 11, 1), client.children.filter(
            name='Стэн').first().birthday)
        ClientChild.objects.update_or_create(**{
            'name': 'Картменез',
            'client_id': client.id,
            'age': '5',
            'celebrate_date': '2015-11-28'
        })
        self.assertEqual(2, len(client.children.all()))
        self.assertEqual(5, client.children.first().age())
        self.assertEqual(date(2009, 11, 28), client.children.first().birthday)


# ==============================================================================

class ProgramTestCase(TestCase):
    def setUp(self):
        gen_us = UserProfileGenerator()
        gen_us.generate(UserProfileGenerator.ANIMATOR, 4)
        gen_us.generate(UserProfileGenerator.PHOTOGRAPHER, 2)
        gen_prog = ProgramGenerator()
        gen_prog.generate(8)

        self.data = {
            'title': 'Наркоман и Гномик',
            'characters': 'Наркоман, Гномик',
            'num_executors': 2,
            'possible_executors': UserProfile.objects.all_executors()[:4],
        }

    def test_create_program(self):
        program = Program.objects.create(**self.data)
        self.assertEqual(self.data.get('title'), program.title)
        self.assertEqual(4, len(program.possible_executors.all()))
        self.assertNotEqual(6, len(program.possible_executors.all()))
        self.assertEqual(2, program.num_executors)
        self.assertNotEqual(3, program.num_executors)

    def test_create_program_unique(self):
        program = Program.objects.first()
        self.data['title'] = program.title
        with self.assertRaises(IntegrityError):
            Program.objects.create(**self.data)
        self.data['title'] = 'Наркоман и Гномик'

    def test_update_or_create_program(self):
        program = Program.objects.first()
        self.data['title'] = program.title
        len_before = len(Program.objects.all())
        Program.objects.update_or_create(**self.data)
        len_after = len(Program.objects.all())
        self.assertEqual(len_before, len_after)
        program = Program.objects.first()
        self.assertEqual(self.data['characters'], program.characters)
        self.assertEqual(self.data['num_executors'], program.num_executors)
        self.assertEqual(
            [x.user_id for x in self.data['possible_executors']],
            [x.user_id for x in program.possible_executors.all()]
        )
        self.data['title'] = 'Наркоман и Гномик'

    def test_update_or_create_program_price(self):
        from django.db import transaction
        from django.db.models import Q

        program = Program.objects.first()
        program.prices.all().delete()
        ProgramPrice.objects.create(**{
            'duration': 60,
            'price': 500000,
            'program_id': program.id
        })
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                ProgramPrice.objects.create(**{
                    'duration': 60,
                    'price': 876500,
                    'program_id': program.id
                })
        ProgramPrice.objects.update_or_create(**{
            'duration': 60,
            'price': 876500,
            'program_id': program.id
        })
        self.assertEqual(
            876500,
            ProgramPrice.objects.get(
                Q(program_id=program.id) & Q(duration=60)).price)

    def test_get_all_prices(self):
        program = Program.objects.first()
        program.prices.all().delete()

        for i in range(1, 4):
            duration = i * 10
            price = duration * 120
            ProgramPrice.objects.create(**{
                'duration': duration,
                'price': price,
                'program_id': program.id
            })
        program = Program.objects.first()
        self.assertEqual(3, len(program.prices.all()))
        self.assertEqual(
            [(10, 1200), (20, 2400), (30, 3600)],
            [(p.duration, p.price) for p in program.prices.all()])

    def test_get_price_by_duration(self):
        program = Program.objects.first()
        program.prices.all().delete()

        for i in range(1, 4):
            duration = i * 10
            price = duration * 120
            ProgramPrice.objects.create(**{
                'duration': duration,
                'price': price,
                'program_id': program.id
            })
        price = program.get_price(duration=10)
        self.assertEqual(1200, price)
        with self.assertRaises(AttributeError):
            program.get_price(duration=12)


# ==============================================================================

class AdditionalServicesTestCase(TestCase):
    def setUp(self):
        gen_us = UserProfileGenerator()
        gen_us.generate(UserProfileGenerator.ANIMATOR, 4)
        gen_us.generate(UserProfileGenerator.PHOTOGRAPHER, 2)
        gen_serv = AdditionalServicesGenerator()
        gen_serv.generate()

        self.data = {
            'title': 'Супер-пупер сервис',
            'num_executors': 2,
            'possible_executors': UserProfile.objects.all_executors()[:4],
            'price': 555000
        }

    def test_create_service(self):
        data = copy.deepcopy(self.data)
        service = AdditionalService.objects.create(**data)
        self.assertEqual(self.data.get('title'), service.title)
        self.assertNotEqual('Какой-то сервис', service.title)
        self.assertEqual(2, service.num_executors)
        self.assertNotEqual(3, service.num_executors)
        self.assertEqual(4, len(service.possible_executors.all()))
        self.assertNotEqual(6, len(service.possible_executors.all()))
        self.assertEqual(555000, service.price)
        self.assertNotEqual(556000, service.price)

    def test_update_or_create_service(self):
        data = copy.deepcopy(self.data)
        AdditionalService.objects.update_or_create(**data)
        data['num_executors'] = 3
        data['possible_executors'] =\
            UserProfile.objects.all_executors()[:3:-1]
        data['price'] = 666000
        service = AdditionalService.objects.update_or_create(**data)
        self.assertEqual(self.data['title'], service.title)
        self.assertEqual(data['num_executors'], service.num_executors)
        self.assertEqual(data['price'], service.price)
        self.assertEqual(
            len(data['possible_executors']),
            len(service.possible_executors.all())
        )
        self.assertTrue(all([x in data['possible_executors'] for x in
                             service.possible_executors.all()]))


# ==============================================================================

class DiscountsTestCase(TestCase):
    def test_create_discount(self):
        discount = Discount.objects.create(name='Скидка №666', value=66)
        self.assertEqual('Скидка №666', discount.name)
        self.assertEqual(66, discount.value)

# ==============================================================================

# class OrdersTestCase(TestCase):
#     order_info = {
#         'code': '',
#         'author_id': 2,
#         'client_id': 1,
#         'client_children_id': [1, 2],
#         'celebrate_date': '2015-09-18',
#         'celebrate_time': '15:00:00',
#         'celebrate_place': 'home',
#         'address': 'Minsk, ul.Kalinovskogo',
#         'program_id': 1,
#         'duration': 1,
#         'price': 0,
#         'additional_services_id': [1, 2],
#         'details': 'some details',
#         'executor_comment': 'some comment',
#         'discounts_id': [1, 2],
#         'total_price': 0,
#         'total_price_with_discounts': 0,
#         'status': 'soon'
#     }
#
#     def test_create_order(self):
#         order = Order.objects.create(**self.order_info)
#         self.assertEqual(12, len(order.code))
#         self.assertEqual(self.order_info.get('author_id'), order.author.id)
#         self.assertEqual(self.order_info.get('client_id'), order.client.id)
#         self.assertEqual(len(self.order_info.get('client_children_id')),
#                          len(order.client_children.all()))
#         self.assertEqual(self.order_info.get('celebrate_date'),
#                          order.celebrate_date)
#         self.assertEqual(self.order_info.get('celebrate_time'),
#                          order.celebrate_time)
#         self.assertEqual(self.order_info.get('celebrate_place'),
#                          order.celebrate_place)
#         self.assertEqual(self.order_info.get('address'), order.address)
#         self.assertEqual(self.order_info.get('program_id'), order.program.id)
#         self.assertEqual(self.order_info.get('duration'), order.duration)
#         self.assertEqual(self.order_info.get('price'), order.price)
#         self.assertEqual(len(self.order_info.get('additional_services_id')),
#                          len(order.additional_services.all()))
#         self.assertEqual(self.order_info.get('details'), order.details)
#         self.assertEqual(self.order_info.get('executor_comment'),
#                          order.executor_comment)
#         self.assertEqual(len(self.order_info.get('discounts_id')),
#                          len(order.discounts.all()))
#         self.assertEqual(self.order_info.get('total_price'), order.total_price)
#         self.assertEqual(self.order_info.get('total_price_with_discounts'),
#                          order.total_price_with_discounts)
#         self.assertEqual(self.order_info.get('status'), order.status)

# ==============================================================================
