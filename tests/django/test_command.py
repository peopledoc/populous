

def test_call_command(capsys):
    import django
    from django.core.management import call_command

    call_command('populous', 'auth', 'app')

    out, err = capsys.readouterr()
    assert out == """items:
- name: Permission
  table: auth_permission
  fields:
    name:
      generator: Text
      min_length: 1
      max_length: 255
    content_type: null
    codename:
      generator: Text
      min_length: 1
      max_length: 100
- name: Group
  table: auth_group
  fields:
    name:
      generator: Text
      min_length: 1
      max_length: 80
      unique: true
- name: User
  table: auth_user
  fields:
    password:
      generator: Text
      min_length: 1
      max_length: 128
    last_login:
      generator: Date
      nullable: true
    is_superuser:
      generator: Boolean
    username:
      generator: Text
      min_length: 1
      max_length: {username_length}
      unique: true
    first_name:
      generator: Text
      min_length: 0
      max_length: 30
    last_name:
      generator: Text
      min_length: 0
      max_length: 30
    email:
      generator: Email
      min_length: 0
      max_length: 254
    is_staff:
      generator: Boolean
    is_active:
      generator: Boolean
    date_joined:
      generator: Date
- name: Test
  table: app_test
  fields:
    bigint:
      generator: Integer
      min: -9223372036854775808
      max: 9223372036854775807
    null_bigint:
      generator: Integer
      min: -9223372036854775808
      max: 9223372036854775807
      nullable: true
    boolean:
      generator: Boolean
    char:
      generator: Text
      min_length: 1
      max_length: 42
    blank_char:
      generator: Text
      min_length: 0
      max_length: 100
    date:
      generator: Date
    date_auto_now:
      generator: Date
      past: true
      future: false
    date_auto_now_add:
      generator: Date
      past: true
      future: false
    datetime:
      generator: Date
    email:
      generator: Email
      min_length: 1
      max_length: 254
    generic_ip:
      generator: IP
      ipv4: true
      ipv6: true
    ip_v4:
      generator: IP
      ipv4: true
      ipv6: false
    ip_v6:
      generator: IP
      ipv4: false
      ipv6: true
    integer:
      generator: Integer
      min: -2147483648
      max: 2147483647
    null_boolean:
      generator: Boolean
      nullable: true
    positive_int:
      generator: Integer
      min: 0
      max: 2147483647
    positive_small_int:
      generator: Integer
      min: 0
      max: 32767
    small_integer:
      generator: Integer
      min: -32768
      max: 32767
    text:
      generator: Text
      min_length: 1
    url:
      generator: URL
      min_length: 1
      max_length: 200
    uuid:
      generator: UUID
      unique: false
    char_choices:
      generator: Choices
      choices: [foo, bar]
    int_choices:
      generator: Choices
      choices: [1, 2]
""".format(
        username_length=30 if django.VERSION < (1, 10) else 150
    )
