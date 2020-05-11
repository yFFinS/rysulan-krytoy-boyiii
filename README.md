Симуляция, использующая архитектуру ECS https://en.wikipedia.org/wiki/Entity_component_system    
=
Имеет собственного настраиваемого vk бота. Работает как сообщество, но можно добавить в беседу. 

Существа делятся на команды, размножаются, пытаются выжить. Умирают от голода, драк, или от старости.

**Запуск**: *main.py*

**Настройка**:  
В файле bot.properties вы пишите токен своего сообщества,  
требуется только отправка сообщений (если не получится, то попробуйте все остальное).  
Ещё нужно id сообщества.  
Также можно написать через ; id людей, у которых будет доступ к командан разработчика в боте.

  
**Требования**:  
*pygame* https://www.pygame.org/ - pip install pygame  
*sqlalchemy* https://www.sqlalchemy.org/ - pip install sqlalchemy  
*vk_api* https://vk-api.readthedocs.io/en/latest/ - pip install vk_api  

**Python 3.7 или выше**
