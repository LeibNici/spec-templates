# Backend (Spring MessageSource)

## 四、后端实现（Spring MessageSource）

### 4.1 资源文件结构

```
src/main/resources/
└── i18n/
    ├── messages.properties           ← 默认（zh_CN）
    ├── messages_zh_CN.properties
    └── messages_en_US.properties
```

### 4.2 application.yml

```yaml
spring:
  messages:
    basename: i18n/messages
    encoding: UTF-8
    fallback-to-system-locale: false
    default-locale: zh-CN
    cache-duration: PT1H  # 缓存 1h，dev 改为 PT0S
```

### 4.3 properties 内容

```properties
# messages_zh_CN.properties
user.notfound=用户 {0} 不存在
order.cannot.cancel=订单已发货，无法取消
validation.user.name.notblank=用户名不能为空
validation.user.email.format=邮箱格式不正确
common.success=操作成功
common.error.system=系统繁忙，请稍后再试
```

```properties
# messages_en_US.properties
user.notfound=User {0} not found
order.cannot.cancel=Order already shipped, cannot cancel
validation.user.name.notblank=Username cannot be blank
validation.user.email.format=Invalid email format
common.success=Success
common.error.system=System busy, please retry later
```

### 4.4 LocaleResolver 配置

```java
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    @Bean
    public LocaleResolver localeResolver() {
        AcceptHeaderLocaleResolver resolver = new AcceptHeaderLocaleResolver();
        resolver.setSupportedLocales(List.of(Locale.SIMPLIFIED_CHINESE, Locale.US));
        resolver.setDefaultLocale(Locale.SIMPLIFIED_CHINESE);
        return resolver;
    }
}
```

### 4.5 业务异常携带 i18n key

```java
// BusinessException.java
@Getter
public class BusinessException extends RuntimeException {
    private final String code;       // i18n key 或错误码
    private final Object[] args;

    public BusinessException(String code, Object... args) {
        super(code);
        this.code = code;
        this.args = args;
    }
}

// 抛出
throw new BusinessException("user.notfound", userId);
```

### 4.6 GlobalExceptionHandler 翻译

```java
@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {

    private final MessageSource messageSource;

    @ExceptionHandler(BusinessException.class)
    public R<?> handle(BusinessException e, Locale locale) {
        String msg = messageSource.getMessage(e.getCode(), e.getArgs(), e.getCode(), locale);
        return R.fail(e.getCode(), msg);
    }
}
```

### 4.7 Bean Validation 消息

```java
public class UserCreateDTO {
    @NotBlank(message = "{validation.user.name.notblank}")
    private String name;

    @Email(message = "{validation.user.email.format}")
    private String email;
}
```

需要在 application.yml 让 Hibernate Validator 用 Spring MessageSource：

```java
@Bean
public LocalValidatorFactoryBean validator(MessageSource messageSource) {
    LocalValidatorFactoryBean factory = new LocalValidatorFactoryBean();
    factory.setValidationMessageSource(messageSource);
    return factory;
}
```
