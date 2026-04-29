## 六、覆盖率门禁

### 起步阶段（推荐）

- **不强制覆盖率**
- 但要求**核心业务方法**（写操作 / 状态流转 / 计算）必须有测试

### 团队稳定后

| 模块类型 | 行覆盖率门禁 | 工具 |
|---|---|---|
| 核心业务（order / inventory） | **80%** | JaCoCo |
| 工具类（utils / common） | **90%** | 同上 |
| Controller / Mapper | **60%**（间接覆盖即可） | 同上 |
| DTO / VO / Entity | **不强制** | 同上 |

### Maven JaCoCo 集成

```xml
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>${jacoco.version}</version>
    <executions>
        <execution>
            <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>verify</phase>
            <goals><goal>report</goal></goals>
        </execution>
        <execution>
            <id>check</id>
            <goals><goal>check</goal></goals>
            <configuration>
                <rules>
                    <rule>
                        <element>BUNDLE</element>
                        <limits>
                            <limit>
                                <counter>LINE</counter>
                                <minimum>0.70</minimum>
                            </limit>
                        </limits>
                    </rule>
                </rules>
            </configuration>
        </execution>
    </executions>
</plugin>
```
