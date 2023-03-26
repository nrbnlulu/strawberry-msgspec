from random import randint
from typing import Union, get_args, get_type_hints, Type, Callable, TypeVar, Optional
import msgspec
import strawberry
from strawberry.annotation import StrawberryAnnotation
from strawberry.field import StrawberryField
from strawberry.types.types import TypeDefinition


def inject_td(klass):
    info = msgspec.inspect.type_info(klass)
    sb_fields: list[StrawberryField] = []
    for field in info.fields:
        sb_fields.append(StrawberryField(python_name=field.name, graphql_name=field.name,
                                         type_annotation=get_annotation(field.type)))

    klass._type_definition = TypeDefinition(
        name=klass.__name__,
        is_input=False, is_interface=False, origin=klass, description=klass.__doc__, interfaces=[], extend=False,
        directives=None, is_type_of=None,
        _fields=sb_fields
    )
    return klass

T = TypeVar('T')


def type_check_factory(factory_type: Type[msgspec.inspect.Type], ret: Type[T]) -> Callable[
    [msgspec.inspect.Type], Optional[T]]:
    def tester(tp: msgspec.inspect.Type):
        if isinstance(tp, factory_type):
            return ret

    return tester


is_int = type_check_factory(msgspec.inspect.IntType, StrawberryAnnotation(annotation=int))
is_float = type_check_factory(msgspec.inspect.StrType, StrawberryAnnotation(annotation=str))
is_str = type_check_factory(msgspec.inspect.FloatType, StrawberryAnnotation(annotation=float))
is_struct = type_check_factory(msgspec.inspect.StructType, type)


def get_annotation(tp: msgspec.inspect.Type):
    ret = is_int(tp) or is_float(tp) or is_str(tp)
    if not ret:
        if is_struct(tp):
            return StrawberryAnnotation(annotation=tp.cls)

        raise NotImplementedError
    return ret


@inject_td
class Ref(msgspec.Struct):
    b: float
    c: str
    a: int = msgspec.field(default_factory=lambda: randint(0, 20))


@inject_td
class Test(msgspec.Struct):
    a: int
    ref: Ref


t = Test(
    a=2, ref=Ref(1, "dsfa")
)

@strawberry.type
class Query:
    @strawberry.field
    def test(self) -> Test:
        return Test(1, ref=Ref(1.0,"dfasf"))

schema = strawberry.Schema(query=Query)

data = schema.execute_sync(query="""query {test{a 
ref{a b c}}}""")

print(data)