"""Python class representations of OpenRPC and JSON Schema objects."""

from __future__ import annotations

__all__ = (
    "APIKeyAuth",
    "BearerAuth",
    "Components",
    "Contact",
    "ContentDescriptor",
    "Error",
    "Example",
    "ExamplePairing",
    "ExternalDocumentation",
    "Info",
    "License",
    "Link",
    "Method",
    "OAuth2",
    "OAuth2Flow",
    "OAuth2FlowType",
    "OpenRPC",
    "ParamStructure",
    "RPCPermissionError",
    "Reference",
    "Schema",
    "SchemaType",
    "Server",
    "ServerVariable",
    "Tag",
)

from enum import Enum
from typing import Any, Callable, Literal, Optional, TypeVar, Union

from pydantic import BaseModel, Field

SchemaType = Union["Schema", bool]
CallableType = TypeVar("CallableType", bound=Callable[..., Any])


class ParamStructure(Enum):
    """OpenRPC method param structure options."""

    BY_NAME = "by-name"
    BY_POSITION = "by-position"
    EITHER = "either"


class Info(BaseModel):
    """The object provides metadata about the API.

    The metadata MAY be used by the clients if needed, and MAY be presented in editing
    or documentation generation tools for convenience.
    """

    title: str
    """The title of the application."""

    description: Optional[str] = None
    """
    A verbose description of the application. GitHub Flavored Markdown syntax MAY be
    used for rich text representation.
    """

    terms_of_service: Optional[str] = Field(default=None, alias="termsOfService")
    """A URL to the Terms of Service for the API. MUST be in the format of a URL."""

    contact: Optional[Contact] = None
    """The contact information for the exposed API."""

    license_: Optional[License] = Field(default=None, alias="license")
    """The license information for the exposed API."""

    version: str
    """
    The version of the OpenRPC document (which is distinct from the OpenRPC
    Specification version or the API implementation version).
    """


class Contact(BaseModel):
    """Contact information for the exposed API."""

    name: Optional[str] = None
    """The identifying name of the contact person/organization."""

    url: Optional[str] = None
    """The URL pointing to the contact information. MUST be in the format of a URL."""

    email: Optional[str] = None
    """
    The email address of the contact person/organization. MUST be in the format of an
    email address.
    """


class License(BaseModel):
    """License information for the exposed API."""

    name: str
    """The license name used for the API."""

    url: Optional[str] = None
    """A URL to the license used for the API. MUST be in the format of a URL."""


class Server(BaseModel):
    """An object representing a Server."""

    name: str
    """A name to be used as the cannonical name for the server."""

    url: str
    """
    A URL to the target host. This URL supports Server Variables and MAY be relative, to
    indicate that the host location is relative to the location where the OpenRPC
    document is being served. Server Variables are passed into the Runtime Expression to
    produce a server URL.
    """

    summary: Optional[str] = None
    """A short summary of what the server is."""

    description: Optional[str] = None
    """
    String describing the host designated by the URL. GitHub Flavored Markdown syntax
    MAY be used for rich text representation.
    """

    variables: Optional[dict[str, ServerVariable]] = None
    """
    A map between a variable name and its value. The value is passed into the Runtime
    Expression to produce a server URL.
    """


class ServerVariable(BaseModel):
    """Represents a Server Variable for server URL template substitution."""

    enum: Optional[list[str]] = None
    """
    An enumeration of string values to be used if the substitution options are from a
    limited set.
    """

    default: str
    """
    The default value to use for substitution, which SHALL be sent if an alternate value
    is not supplied. Note this behavior is different than the Schema Object’s treatment
    of default values, because in those cases parameter values are optional.
    """

    description: Optional[str] = None
    """
    Description for the server variable. GitHub Flavored Markdown syntax MAY be used for
    rich text representation.
    """


class Method(BaseModel):
    """Describes the interface for the given method name."""

    name: str
    """
    The cannonical name for the method. The name MUST be unique within the methods
    array.
    """

    tags: Optional[list[Tag]] = None
    """
    A list of tags for API documentation control. Tags can be used for logical grouping
    of methods by resources or any other qualifier.
    """

    summary: Optional[str] = None
    """A short summary of what the method does."""

    description: Optional[str] = None
    """
    A verbose explanation of the method behavior. GitHub Flavored Markdown syntax MAY be
    used for rich text representation.
    """

    external_docs: Optional[ExternalDocumentation] = Field(
        default=None, alias="externalDocs"
    )
    """Additional external documentation for this method."""

    params: list[ContentDescriptor]
    """
    A list of parameters that are applicable for this method. The list MUST NOT include
    duplicated parameters and therefore require name to be unique. The list can use the
    Reference Object to link to parameters that are defined by the Content Descriptor
    Object. All optional params (content descriptor objects with “required”: false) MUST
    be positioned after all required params in the list.
    """

    result: ContentDescriptor
    """
    The description of the result returned by the method. If defined, it MUST be a
    Content Descriptor or Reference Object. If undefined, the method MUST only be used
    as a notification.
    """

    deprecated: Optional[bool] = False
    """
    Declares this method to be deprecated. Consumers SHOULD refrain from usage of the
    declared method. Default value is false.
    """

    servers: Optional[list[Server]] = None
    """
    An alternative servers array to service this method. If an alternative servers array
    is specified at the Root level, it will be overridden by this value.
    """

    errors: Optional[list[Error]] = None
    """
    A list of custom application defined errors that MAY be returned. The Errors MUST
    have unique error codes.
    """

    links: Optional[list[Link]] = None
    """A  list of possible links from this method call."""

    param_structure: Optional[ParamStructure] = Field(
        default=None, alias="paramStructure"
    )
    """
    The expected format of the parameters. As per the JSON-RPC 2.0 specification, the
    params of a JSON-RPC request object may be an array, object, or either (represented
    as by-position, by-name, and either respectively). When a method has a
    paramStructure value of by-name, callers of the method MUST send a JSON-RPC request
    object whose params field is an object. Further, the key names of the params object
    MUST be the same as the contentDescriptor.names for the given method. Defaults to
    "either".
    """

    examples: Optional[list[ExamplePairing]] = None
    """
    Array of Example Pairing Objects where each example includes a valid
    params-to-result Content Descriptor pairing.
    """

    x_security: Optional[dict[str, list[str]]] = Field(default=None, alias="x-security")
    """
    Extension field describing security scheme and scopes required to call this method.
    """

    x_scopes: list[Scope] = Field(default_factory=list, alias="x-scopes")
    """
    Extension listing required permission scopes to call this method.
    """


class ContentDescriptor(BaseModel):
    """Describes either parameters or result.

    Content Descriptors are objects that do just as they suggest - describe content.
    They are reusable ways of describing either parameters or result. They MUST have a
    schema.
    """

    name: str
    """
    Name of the content that is being described. If the content described is a method
    parameter assignable by-name, this field SHALL define the parameter’s key (ie name).
    """

    summary: Optional[str] = None
    """A short summary of the content that is being described."""

    description: Optional[str] = None
    """
    A verbose explanation of the content descriptor behavior. GitHub Flavored Markdown
    syntax MAY be used for rich text representation.
    """

    required: Optional[bool] = None
    """Determines if the content is a required field. Default value is false."""

    schema_: SchemaType = Field(alias="schema")
    """Schema that describes the content."""

    deprecated: bool = False
    """
    Specifies that the content is deprecated and SHOULD be transitioned out of usage.
    Default value is false.
    """


class Schema(BaseModel):
    """JSON Schema object."""

    id: Optional[str] = Field(alias="$id", default=None)
    """ID of the schema."""

    title: Optional[str] = None
    """Title this schema."""

    format: Optional[str] = None
    """Format of a string, e.g. "date"."""

    enum: Optional[list[Any]] = None
    """
    This array SHOULD have at least one element. Elements in the array SHOULD be unique.

    An instance validates successfully against this keyword if its value is equal to one
    of the elements in this keyword's array value.
    """

    type: Optional[Union[str, list[str]]] = None
    """
    String values MUST be one of the six primitive types ("null", "boolean", "object",
    "array", "number", or "string"), or "integer" which matches any number with a zero
    fractional part.

    An instance validates if and only if the instance is in any of the sets listed for
    this keyword.

    If it is an array, elements of the array MUST be unique.
    """

    all_of: Optional[list[SchemaType]] = Field(alias="allOf", default=None)
    """
    An instance validates successfully against this keyword if it validates successfully
    against all schemas defined by this keyword's value.
    """

    any_of: Optional[list[SchemaType]] = Field(alias="anyOf", default=None)
    """
    An instance validates successfully against this keyword if it validates successfully
    against at least one schema defined by this keyword's value. Note that when
    annotations are being collected, all subschemas MUST be examined so that annotations
    are collected from each subschema that validates successfully.
    """

    one_of: Optional[list[SchemaType]] = Field(alias="oneOf", default=None)
    """
    An instance validates successfully against this keyword if it validates successfully
    against exactly one schema defined by this keyword's value.
    """

    not_: Optional[SchemaType] = Field(alias="not", default=None)
    """
    An instance is valid against this keyword if it fails to validate successfully
    against the schema defined by this keyword.
    """

    pattern: Optional[str] = None
    """
    This string SHOULD be a valid regular expression, according to the ECMA-262 regular
    expression dialect.

    A string instance is considered valid if the regular expression matches the instance
    successfully.
    """

    minimum: Optional[float] = None
    """
    An inclusive lower limit for a numeric instance.

    If the instance is a number, then this keyword validates only if the instance is
    greater than or exactly equal to "minimum".
    """

    maximum: Optional[float] = None
    """
    An inclusive upper limit for a numeric instance.

    If the instance is a number, then this keyword validates only if the instance is
    less than or exactly equal to "maximum".
    """

    exclusive_minimum: Optional[float] = Field(alias="exclusiveMinimum", default=None)
    """
    Exclusive lower limit for a numeric instance.

    If the instance is a number, then the instance is valid only if it has a value
    strictly greater than (not equal to) "exclusiveMinimum".
    """

    exclusive_maximum: Optional[float] = Field(alias="exclusiveMaximum", default=None)
    """
    Exclusive upper limit for a numeric instance.

    If the instance is a number, then the instance is valid only if it has a value
    strictly less than (not equal to) "exclusiveMaximum".
    """

    multiple_of: Optional[float] = Field(alias="multipleOf", default=None)
    """
    The value MUST be greater than 0.

    A numeric instance is valid only if division by this keyword's value results in an
    integer.
    """

    min_length: Optional[int] = Field(alias="minLength", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    A string instance is valid against this keyword if its length is greater than, or
    equal to, the value of this keyword.

    The length of a string instance is defined as the number of its characters as
    defined by RFC 8259.

    Omitting this keyword has the same behavior as a value of 0.
    """

    max_length: Optional[int] = Field(alias="maxLength", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    A string instance is valid against this keyword if its length is less than, or equal
    to, the value of this keyword.

    The length of a string instance is defined as the number of its characters as
    defined by RFC 8259.
    """

    properties: Optional[dict[str, SchemaType]] = None
    """
    Validation succeeds if, for each name that appears in both the instance and as a
    name within this keyword's value, the child instance for that name successfully
    validates against the corresponding schema.

    The annotation result of this keyword is the set of instance property names matched
    by this keyword.

    Omitting this keyword has the same assertion behavior as an empty object.
    """

    pattern_properties: Optional[dict[str, SchemaType]] = Field(
        alias="patternProperties", default=None
    )
    """
    Each property name of this object SHOULD be a valid regular expression, according to
    the ECMA-262 regular expression dialect. Each property value of this object MUST be
    a valid JSON Schema.

    Validation succeeds if, for each instance name that matches any regular expressions
    that appear as a property name in this keyword's value, the child instance for that
    name successfully validates against each schema that corresponds to a matching
    regular expression.

    The annotation result of this keyword is the set of instance property names matched
    by this keyword.

    Omitting this keyword has the same assertion behavior as an empty object.
    """

    additional_properties: Optional[SchemaType] = Field(
        alias="additionalProperties", default=None
    )
    """
    The behavior of this keyword depends on the presence and annotation results of
    "properties" and "patternProperties" within the same schema object. Validation with
    "additionalProperties" applies only to the child values of instance names that do
    not appear in the annotation results of either "properties" or "patternProperties".

    For all such properties, validation succeeds if the child instance validates against
    the "additionalProperties" schema.

    The annotation result of this keyword is the set of instance property names
    validated by this keyword's subschema.

    Omitting this keyword has the same assertion behavior as an empty schema.

    Implementations MAY choose to implement or optimize this keyword in another way that
    produces the same effect, such as by directly checking the names in "properties" and
    the patterns in "patternProperties" against the instance property set.
    Implementations that do not support annotation collection MUST do so.
    """

    property_names: Optional[SchemaType] = Field(alias="propertyNames", default=None)
    """
    If the instance is an object, this keyword validates if every property name in the
    instance validates against the provided schema. Note the property name that the
    schema is testing will always be a string.

    Omitting this keyword has the same behavior as an empty schema.
    """

    min_properties: Optional[int] = Field(alias="minProperties", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    An object instance is valid against "minProperties" if its number of properties is
    greater than, or equal to, the value of this keyword.

    Omitting this keyword has the same behavior as a value of 0.
    """

    max_properties: Optional[int] = Field(alias="maxProperties", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    An object instance is valid against "maxProperties" if its number of properties is
    less than, or equal to, the value of this keyword.
    """

    required: Optional[list[str]] = None
    """
    Elements of this array, if any, MUST be unique.

    An object instance is valid against this keyword if every item in the array is the
    name of a property in the instance.

    Omitting this keyword has the same behavior as an empty array.
    """

    defs: Optional[dict[str, SchemaType]] = Field(alias="$defs", default=None)
    """
    The "$defs" keyword reserves a location for schema authors to inline re-usable JSON
    Schemas into a more general schema. The keyword does not directly affect the
    validation result.
    """

    items: Optional[SchemaType] = None
    """
    This keyword applies its subschema to all instance elements at indexes greater than
    the length of the "prefixItems" array in the same schema object, as reported by the
    annotation result of that "prefixItems" keyword. If no such annotation result
    exists, "items" applies its subschema to all instance array elements. [CREF11]

    If the "items" subschema is applied to any positions within the instance array, it
    produces an annotation result of boolean true, indicating that all remaining array
    elements have been evaluated against this keyword's subschema.

    Omitting this keyword has the same assertion behavior as an empty schema.

    Implementations MAY choose to implement or optimize this keyword in another way that
    produces the same effect, such as by directly checking for the presence and size of
    a "prefixItems" array. Implementations that do not support annotation collection
    MUST do so.
    """

    prefix_items: Optional[list[SchemaType]] = Field(alias="prefixItems", default=None)
    """
    Validation succeeds if each element of the instance validates against the schema at
    the same position, if any. This keyword does not constrain the length of the array.
    If the array is longer than this keyword's value, this keyword validates only the
    prefix of matching length.

    This keyword produces an annotation value which is the largest index to which this
    keyword applied a subschema. The value MAY be a boolean true if a subschema was
    applied to every index of the instance, such as is produced by the "items" keyword.
    This annotation affects the behavior of "items" and "unevaluatedItems".

    Omitting this keyword has the same assertion behavior as an empty array.
    """

    contains: Optional[SchemaType] = None
    """
    An array instance is valid against "contains" if at least one of its elements is
    valid against the given schema. The subschema MUST be applied to every array element
    even after the first match has been found, in order to collect annotations for use
    by other keywords. This is to ensure that all possible annotations are collected.

    Logically, the validation result of applying the value subschema to each item in the
    array MUST be ORed with "false", resulting in an overall validation result.

    This keyword produces an annotation value which is an array of the indexes to which
    this keyword validates successfully when applying its subschema, in ascending order.
    The value MAY be a boolean "true" if the subschema validates successfully when
    applied to every index of the instance. The annotation MUST be present if the
    instance array to which this keyword's schema applies is empty.
    """

    min_contains: Optional[int] = Field(alias="minContains", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    If "contains" is not present within the same schema object, then this keyword has no
    effect.

    An instance array is valid against "minContains" in two ways, depending on the form
    of the annotation result of an adjacent "contains" keyword. The first way is if the
    annotation result is an array and the length of that array is greater than or equal
    to the "minContains" value. The second way is if the annotation result is a boolean
    "true" and the instance array length is greater than or equal to the "minContains"
    value.

    A value of 0 is allowed, but is only useful for setting a range of occurrences from
    0 to the value of "maxContains". A value of 0 with no "maxContains" causes
    "contains" to always pass validation.

    Omitting this keyword has the same behavior as a value of 1.
    """

    max_contains: Optional[int] = Field(alias="maxContains", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    If "contains" is not present within the same schema object, then this keyword has no
    effect.

    An instance array is valid against "maxContains" in two ways, depending on the form
    of the annotation result of an adjacent "contains" keyword. The first way is if the
    annotation result is an array and the length of that array is less than or equal to
    the "maxContains" value. The second way is if the annotation result is a boolean
    "true" and the instance array length is less than or equal to the "maxContains"
    value.
    """

    min_items: Optional[int] = Field(alias="minItems", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    An array instance is valid against "minItems" if its size is greater than, or equal
    to, the value of this keyword.

    Omitting this keyword has the same behavior as a value of 0.
    """

    max_items: Optional[int] = Field(alias="maxItems", default=None)
    """
    The value of this keyword MUST be a non-negative integer.

    An array instance is valid against "maxItems" if its size is less than, or equal to,
    the value of this keyword.
    """

    unique_items: Optional[bool] = Field(alias="uniqueItems", default=None)
    """
    If false, the instance validates successfully. If true, the instance validates
    successfully if all of its elements are unique.

    Omitting this keyword has the same behavior as a value of false.
    """

    ref: Optional[str] = Field(alias="$ref", default=None)
    """Reference to a schema."""

    description: Optional[str] = None
    """Explanation about the purpose of the instance described by this schema."""

    deprecated: Optional[bool] = None
    """
    When multiple occurrences of this keyword are applicable to a single sub-instance,
    applications SHOULD consider the instance location to be deprecated if any
    occurrence specifies a true value.

    If "deprecated" has a value of boolean true, it indicates that applications SHOULD
    refrain from usage of the declared property. It MAY mean the property is going to be
    removed in the future.

    A root schema containing "deprecated" with a value of true indicates that the entire
    resource being described MAY be removed in the future.

    The "deprecated" keyword applies to each instance location to which the schema
    object containing the keyword successfully applies. This can result in scenarios
    where every array item or object property is deprecated even though the containing
    array or object is not.

    Omitting this keyword has the same behavior as a value of false.
    """

    default: Optional[Any] = None
    """
    When multiple occurrences of this keyword are applicable to a single sub-instance,
    implementations SHOULD remove duplicates.

    This keyword can be used to supply a default JSON value associated with a particular
    schema. It is RECOMMENDED that a default value be valid against the associated
    schema.
    """

    examples: Optional[list[Any]] = None
    """
    When multiple occurrences of this keyword are applicable to a single sub-instance,
    implementations MUST provide a flat array of all values rather than an array of
    arrays.

    This keyword can be used to provide sample JSON values associated with a particular
    schema, for the purpose of illustrating usage. It is RECOMMENDED that these values
    be valid against the associated schema.

    Implementations MAY use the value(s) of "default", if present, as an additional
    example. If "examples" is absent, "default" MAY still be used in this manner.
    """

    read_only: Optional[bool] = Field(alias="readOnly", default=None)
    """
    If "readOnly" has a value of boolean true, it indicates that the value of the
    instance is managed exclusively by the owning authority, and attempts by an
    application to modify the value of this property are expected to be ignored or
    rejected by that owning authority.

    An instance document that is marked as "readOnly" for the entire document MAY be
    ignored if sent to the owning authority, or MAY result in an error, at the
    authority's discretion.

    For example, "readOnly" would be used to mark a database-generated serial number as
    read-only.
    """

    write_only: Optional[bool] = Field(alias="writeOnly", default=None)
    """
    If "writeOnly" has a value of boolean true, it indicates that the value is never
    present when the instance is retrieved from the owning authority. It can be present
    when sent to the owning authority to update or create the document (or the resource
    it represents), but it will not be included in any updated or newly created version
    of the instance.

    An instance document that is marked as "writeOnly" for the entire document MAY be
    returned as a blank document of some sort, or MAY produce an error upon retrieval,
    or have the retrieval request ignored, at the authority's discretion.

    For example, "readOnly" would be used to mark a database-generated serial number as
    read-only. while "writeOnly" would be used to mark a password input field.
    """

    const: Optional[Any] = None
    """
    Use of this keyword is functionally equivalent to an "enum" with a single value.

    An instance validates successfully against this keyword if its value is equal to the
    value of the keyword.
    """

    dependent_required: Optional[dict[str, list[str]]] = Field(
        alias="dependentRequired", default=None
    )
    """
    Elements in each array, if any, MUST be unique.

    This keyword specifies properties that are required if a specific other property is
    present. Their requirement is dependent on the presence of the other property.

    Validation succeeds if, for each name that appears in both the instance and as a
    name within this keyword's value, every item in the corresponding array is also the
    name of a property in the instance.

    Omitting this keyword has the same behavior as an empty object.
    """

    dependent_schemas: Optional[dict[str, SchemaType]] = Field(
        alias="dependentSchemas", default=None
    )
    """
    This keyword specifies subschemas that are evaluated if the instance is an object
    and contains a certain property.

    If the object key is a property in the instance, the entire instance must validate
    against the subschema. Its use is dependent on the presence of the property.

    Omitting this keyword has the same behavior as an empty object.
    """

    if_: Optional[SchemaType] = Field(alias="if", default=None)
    """
    This validation outcome of this keyword's subschema has no direct effect on the
    overall validation result. Rather, it controls which of the "then" or "else"
    keywords are evaluated.

    Instances that successfully validate against this keyword's subschema MUST also be
    valid against the subschema value of the "then" keyword, if present.

    Instances that fail to validate against this keyword's subschema MUST also be valid
    against the subschema value of the "else" keyword, if present.

    If annotations are being collected, they are collected from this keyword's subschema
    in the usual way, including when the keyword is present without either "then" or
    "else".
    """

    then: Optional[SchemaType] = None
    """
    When "if" is present, and the instance successfully validates against its subschema,
    then validation succeeds against this keyword if the instance also successfully
    validates against this keyword's subschema.

    This keyword has no effect when "if" is absent, or when the instance fails to
    validate against its subschema. Implementations MUST NOT evaluate the instance
    against this keyword, for either validation or annotation collection purposes, in
    such cases.
    """

    else_: Optional[SchemaType] = Field(alias="else", default=None)
    """
    When "if" is present, and the instance fails to validate against its subschema, then
    validation succeeds against this keyword if the instance successfully validates
    against this keyword's subschema.

    This keyword has no effect when "if" is absent, or when the instance successfully
    validates against its subschema. Implementations MUST NOT evaluate the instance
    against this keyword, for either validation or annotation collection purposes, in
    such cases.
    """

    schema_: Optional[str] = Field(alias="$schema", default=None)
    """
    The "$schema" keyword is both used as a JSON Schema dialect identifier and as the
    identifier of a resource which is itself a JSON Schema, which describes the set of
    valid schemas written for this particular dialect.

    The value of this keyword MUST be a URI (containing a scheme) and this URI MUST be
    normalized. The current schema MUST be valid against the meta-schema identified by
    this URI.

    If this URI identifies a retrievable resource, that resource SHOULD be of media type
    "application/schema+json".

    The "$schema" keyword SHOULD be used in the document root schema object, and MAY be
    used in the root schema objects of embedded schema resources. It MUST NOT appear in
    non-resource root schema objects. If absent from the document root schema, the
    resulting behavior is implementation-defined.

    Values for this property are defined elsewhere in this and other documents, and by
    other parties.
    """


class ExamplePairing(BaseModel):
    """The Example Pairing object consists of a set of example params and result.

    The result is what you can expect from the JSON-RPC service given the exact params.
    Consists of a set of example params and result.
    """

    name: str
    """Name for the example pairing."""

    description: Optional[str] = None
    """A verbose explanation of the example pairing."""

    summary: Optional[str] = None
    """Short description for the example pairing."""

    params: list[Example]
    """Example parameters."""

    result: Optional[Example] = None
    """
    Example result. When undefined, the example pairing represents usage of the method
    as a notification.
    """

    @staticmethod
    def example(
        name: str,
        params: list[Any] | dict[str, Any] | None,
        result: Any | OpenRPCError,
        summary: str | None = None,
        description: str | None = None,
    ) -> ExamplePairing:
        """Get example pairing object for given params and result.

        :param name: Name of the example pairing.
        :param params: Params of the request.
        :param result: Response value.
        :param summary: Summary of the example.
        :param description: Lengthy description of the example.
        :return: The generated Example pairing object.
        """
        if isinstance(params, dict):
            param_examples: list[Example] = []
        elif isinstance(params, list):
            param_examples = []
        else:
            param_examples = []
        if isinstance(result, OpenRPCError):
            summary, description = _get_summary_and_description(result)
            result_example = Example(
                name=result.__qualname__,
                summary=summary,
                description=description,
                value=result.get_error_object().model_dump(),
            )
        else:
            result_example = Example(name="Result", value=result)
        return ExamplePairing(
            name=name,
            description=description,
            summary=summary,
            params=param_examples,
            result=result_example,
        )


def _get_summary_and_description(error: OpenRPCError) -> tuple[str | None, str | None]:
    doc_string = error.__doc__
    if doc_string is None:
        return None, None
    if len(lines := doc_string.split("\n")) > 1:
        return lines[0], "\n".join(lines[1:])
    return doc_string, None


class Example(BaseModel):
    """Example that is intended to match a given Content Descriptor Schema."""

    name: str
    """Cannonical name of the example."""

    summary: Optional[str] = None
    """Short description for the example."""

    description: Optional[str] = None
    """
    A verbose explanation of the example. GitHub Flavored Markdown syntax MAY be used
    for rich text representation.
    """

    value: Optional[Any] = None
    """
    Embedded literal example. The value field and externalValue field are mutually
    exclusive. To represent examples of media types that cannot naturally represented in
    JSON, use a string value to contain the example, escaping where necessary.
    """

    external_value: Optional[str] = Field(default=None, alias="externalValue")
    """
    A URL that points to the literal example. This provides the capability to reference
    examples that cannot easily be included in JSON documents. The value field and
    externalValue field are mutually exclusive.
    """


class Link(BaseModel):
    """The Link object represents a possible design-time link for a result.

    The presence of a link does not guarantee the caller’s ability to successfully
    invoke it, rather it provides a known relationship and traversal mechanism between
    results and other methods.

    Unlike dynamic links (i.e. links provided in the result payload), the OpenRPC
    linking mechanism does not require link information in the runtime result.

    For computing links, and providing instructions to execute them, a runtime
    expression is used for accessing values in an method and using them as parameters
    while invoking the linked method.
    """

    name: str
    """Cannonical name of the link."""

    description: Optional[str] = None
    """
    A description of the link. GitHub Flavored Markdown syntax MAY be used for rich text
    representation.
    """

    summary: Optional[str] = None
    """Short description for the link."""

    method: Optional[str] = None
    """
    The name of an existing, resolvable OpenRPC method, as defined with a unique method.
    This field MUST resolve to a unique Method Object. As opposed to Open Api, Relative
    method values ARE NOT permitted.
    """

    params: Optional[Any] = None
    """
    A map representing parameters to pass to a method as specified with method. The key
    is the parameter name to be used, whereas the value can be a constant or a runtime
    expression to be evaluated and passed to the linked method.
    """

    server: Optional[Server] = None
    """A server object to be used by the target method."""


class Error(BaseModel):
    """Defines an application level error."""

    code: int
    """A Number that indicates the error type that occurred."""

    message: str
    """
    A String providing a short description of the error.

    The message SHOULD be limited to a concise single sentence.
    """

    data: Optional[Any] = None
    """
    A value that contains additional information about the error.

    The value of this member is defined by the Server (e.g. detailed error information,
    nested errors etc.).
    """


class Components(BaseModel):
    """Holds a set of reusable objects for different aspects of the OpenRPC."""

    content_descriptors: Optional[dict[str, ContentDescriptor]] = Field(
        default=None, alias="contentDescriptors"
    )
    """Object to hold reusable `ContentDescriptor` Objects."""

    schemas: Optional[dict[str, SchemaType]] = None
    """Object to hold reusable `Schema` Objects."""

    examples: Optional[dict[str, Example]] = None
    """Object to hold reusable `Example` Objects."""

    links: Optional[dict[str, Link]] = None
    """Object to hold reusable `Link` Objects."""

    errors: Optional[dict[str, Error]] = None
    """Object to hold reusable `Error` Objects."""

    example_pairing_objects: Optional[dict[str, ExamplePairing]] = Field(
        default=None, alias="examplePairingObjects"
    )
    """Object to hold reusable Example Pairing Objects."""

    tags: Optional[dict[str, Tag]] = None
    """Object to hold reusable `Tag` Objects."""

    x_security_schemes: Optional[dict[str, Union[OAuth2, BearerAuth, APIKeyAuth]]] = (
        Field(default=None, alias="x-securitySchemes")
    )
    """Object to hold reusable Security Scheme Objects."""

    def resolve_reference(self, reference: str) -> Optional[SchemaType]:
        """Get a component schema from a schema reference.

        :param reference: Reference of the schema.
        :return: The schema if it exists, else None.
        """
        ref_path = "#/components/schemas/"
        if not reference.startswith(ref_path) or self.schemas is None:
            return None
        return self.schemas.get(reference.removeprefix(ref_path))


class Tag(BaseModel):
    """Adds metadata to a single tag that is used by the Method Object."""

    name: str
    """The name of the tag."""

    summary: Optional[str] = None
    """A short summary of the tag."""

    description: Optional[str] = None
    """
    A verbose explanation for the tag. GitHub Flavored Markdown syntax MAY be used for
    rich text representation.
    """

    external_docs: Optional[ExternalDocumentation] = Field(
        default=None, alias="externalDocs"
    )
    """Additional external documentation for this tag."""


class ExternalDocumentation(BaseModel):
    """Allows referencing an external resource for extended documentation."""

    description: Optional[str] = None
    """
    A verbose explanation of the target documentation. GitHub Flavored Markdown syntax
    MAY be used for rich text representation.
    """

    url: str
    """The URL for the target documentation. Value MUST be in the format of a URL."""


class Reference(BaseModel):
    """A simple object to allow referencing other components in the specification."""

    ref: str = Field(alias="$ref")
    """The reference string."""


class OpenRPC(BaseModel):
    """The root object of the OpenRPC document.

    The contents of this object represent a whole OpenRPC document. How this object is
    constructed or stored is outside the scope of the OpenRPC Specification.
    """

    openrpc: str
    """
    This string MUST be the semantic version number of the OpenRPC Specification version
    that the OpenRPC document uses. The openrpc field SHOULD be used by tooling
    specifications and clients to interpret the OpenRPC document. This is not related to
    the API info.version string.
    """

    info: Info
    """
    Provides metadata about the API. The metadata MAY be used by tooling as required.
    """

    servers: Union[list[Server], Server] = Server(name="default", url="localhost")
    """
    An array of Server Objects, which provide connectivity information to a target
    server. If the servers property is not provided, or is an empty array, the default
    value would be a Server Object with a url value of localhost.
    """

    methods: list[Method]
    """
    The available methods for the API. While it is required, the array may be empty (to
    handle security filtering, for example).
    """

    components: Optional[Components] = None
    """An element to hold various schemas for the specification."""

    external_docs: Optional[ExternalDocumentation] = Field(
        default=None, alias="externalDocs"
    )
    """Additional external documentation."""


class Scope(BaseModel):
    """Permission scope required to call a method."""

    name: str
    """Name identifying the scope, e.g. `users:read`."""

    description: Optional[str] = None
    """
    Description of the purpose of the scope e.g. `Permission to read list of users.`.
    """


class OAuth2FlowType(Enum):
    """Type of OAuth 2.0 flows."""

    AUTHORIZATION_CODE = "authorizationCode"
    CLIENT_CREDENTIALS = "clientCredentials"
    PASSWORD = "password"  # noqa: S105


class OAuth2Flow(BaseModel):
    """An OAuth 2.0 flow."""

    type: OAuth2FlowType
    authorization_url: Optional[str] = Field(alias="authorizationUrl", default=None)
    refresh_url: Optional[str] = Field(alias="refreshUrl", default=None)
    token_url: Optional[str] = Field(alias="tokenUrl", default=None)
    scopes: dict[str, str] = Field(default_factory=dict)


class OAuth2(BaseModel):
    """Describes OAuth 2.0 security scheme used by an API."""

    type: Literal["oauth2"] = "oauth2"
    flows: list[OAuth2Flow] = Field(min_length=1)
    description: Optional[str] = None


class BearerAuth(BaseModel):
    """Describes Bearer security scheme used by an API."""

    type: Literal["bearer"] = "bearer"
    in_: str = Field(default="header", alias="in")
    name: str = "Authorization"
    description: Optional[str] = None
    scopes: dict[str, str] = Field(default_factory=dict)


class APIKeyAuth(BaseModel):
    """Describes API Key security scheme used by an API."""

    type: Literal["apikey"] = "apikey"
    in_: str = Field(default="header", alias="in")
    name: str = "api_key"
    description: Optional[str] = None
    scopes: dict[str, str] = Field(default_factory=dict)


class OpenRPCError(Exception):
    """Base error for OpenRPC API."""

    def __init__(
        self, code: int, message: str, data: Any | None = None, *args: object
    ) -> None:
        """Instantiate OpenRPC error.

        :param code: A Number that indicates the error type that occurred.
        :param message: A short description of the error.
        :param data: Value that contains additional information about the error.
        :param args: Python `Exeption` arguments.
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(*args)

    def get_error_object(self) -> Error:
        return Error(code=self.code, message=self.message, data=self.data)


class RPCPermissionError(OpenRPCError):
    """Error raised when method caller is missing permissions."""

    def __init__(self, data: str | None = None) -> None:
        super().__init__(-32099, "Permission error", data)
