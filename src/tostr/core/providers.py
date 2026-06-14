from __future__ import annotations
from typing import Optional
from importlib import import_module

class LanguageProvider:
    # Maps language string to (package, builder_class, resolver_class)
    language_map = {
        "java": ("tostr.languages.java.builders", "JavaBuilder", "tostr.core.resolver.JavaDependencyResolver"),
        "python": ("tostr.languages.python.builders", "PythonBuilder", "tostr.core.resolver.PythonDependencyResolver"),
    }

    # Maps file extension to language key in language_map.
    extension_map = {
        ".java": "java",
        ".py": "python",
    }

    @classmethod
    def language_for_extension(cls, ext: str) -> Optional[str]:
        """Resolves a file extension (e.g. '.py') to its language key, or None if unsupported."""
        return cls.extension_map.get(ext.lower()) if ext else None

    @classmethod
    def _language_enabled(cls, registry: "Registry", lang: str) -> bool:
        """In single-language mode (config language != 'auto'), only the configured language is
        parsed. In 'auto' mode every supported language is accepted and routed per-file."""
        configured = (registry.language or "auto").lower()
        return configured == "auto" or configured == lang

    @classmethod
    def get_builder(cls, registry: "Registry", ext: str) -> Optional["BaseBuilder"]:
        """Returns a builder for the file's extension, or None if the extension is
        unsupported or excluded by a single-language configuration."""
        lang = cls.language_for_extension(ext)
        if not lang or not cls._language_enabled(registry, lang):
            return None

        package, builder_name, _ = cls.language_map[lang]
        module = import_module(package)
        builder_class = getattr(module, builder_name)
        return builder_class(registry)

    @classmethod
    def get_resolver(cls, registry: "Registry", ext: str) -> "BaseDependencyResolver":
        """Returns the dependency resolver for the file's extension. Falls back to the
        base (no-op) resolver for extensions without language-specific resolution."""
        lang = cls.language_for_extension(ext)
        if lang and lang in cls.language_map:
            _, _, resolver_path = cls.language_map[lang]
            module_path, class_name = resolver_path.rsplit(".", 1)
            module = import_module(module_path)
            resolver_class = getattr(module, class_name)
            return resolver_class(registry)

        from tostr.core.resolver import BaseDependencyResolver
        return BaseDependencyResolver(registry)
