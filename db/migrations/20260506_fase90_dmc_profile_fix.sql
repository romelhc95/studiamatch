-- Fase 90: DMC Profile Fix — WooCommerce selectors + exclusiones
-- Cambia catalog_link_selector de Elementor (0 resultados) a WooCommerce correcto.
-- Agrega exclusiones para URLs transaccionales WooCommerce.
-- Genérico: el mecanismo institution_site_profiles ya soporta cualquier institución.
-- Nueva institución WooCommerce solo necesita crear perfil con los mismos patrones.

UPDATE institution_site_profiles
SET 
  catalog_link_selector = 'a.woocommerce-LoopProduct-link',
  exclusion_patterns = exclusion_patterns || '["/checkout/", "/mi-cuenta/", "/cart/", "add-to-cart="]'::jsonb
WHERE institution_id = (SELECT id FROM institutions WHERE slug = 'dmc');
