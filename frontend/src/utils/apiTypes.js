/**
 * BuildTrack — shared frontend API types (JS + JSDoc).
 * Mirror of docs/API_CONTRACT.md + docs/DATA_MODEL.md.
 * Backend MUST NOT rename fields without bumping this file's VERSION.
 * @version 1.0.0
 * @baseUrl /api/
 */

// ---------------------------------------------------------------------------
// Enums (string unions — keep in sync with backend choices)
// ---------------------------------------------------------------------------

/** @typedef {"admin"|"client"} UserRole */
/** @typedef {"planned"|"in_progress"|"on_hold"|"completed"|"cancelled"} ProjectStatus */
/** @typedef {"construction"|"renovation"|"design"|"consulting"|"other"} ServiceType */
/** @typedef {"under_10k"|"10k_50k"|"50k_100k"|"over_100k"|"undecided"} BudgetRange */
/** @typedef {"phone"|"email"|"telegram"|"whatsapp"} PreferredContact */
/** @typedef {"new"|"contacted"|"estimated"|"accepted"|"declined"|"expired"} QuoteStatus */

// ---------------------------------------------------------------------------
// Common
// ---------------------------------------------------------------------------

/**
 * DRF paginated list envelope.
 * @template T
 * @typedef {Object} PaginatedResponse
 * @property {number} count
 * @property {string|null} next
 * @property {string|null} previous
 * @property {T[]} results
 */

/**
 * API error envelope.
 * @typedef {Object} ApiError
 * @property {string} [detail]
 * @property {string} [code]
 * @property {Record<string, string[]>} [errors] field-level errors
 */

/**
 * List query params supported on all list endpoints.
 * @typedef {Object} ListParams
 * @property {number} [page]
 * @property {number} [page_size] max 100
 * @property {string} [search]
 * @property {string} [ordering] e.g. "-created_at"
 */

// ---------------------------------------------------------------------------
// User / Auth — /api/auth/
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} email
 * @property {string} full_name
 * @property {string|null} [phone]
 * @property {string|null} [company]
 * @property {UserRole} role
 * @property {boolean} is_staff
 * @property {string} created_at ISO-8601
 * @property {string} [updated_at]
 */

/** @typedef {Object} RegisterPayload
 * @property {string} email
 * @property {string} password min 8 chars
 * @property {string} password_confirm must match password
 * @property {string} full_name
 * @property {string} [phone]
 * @property {string} [company]
 */

/** @typedef {Object} RegisterResponse
 * @property {number} id
 * @property {string} email
 * @property {string} full_name
 * @property {string|null} phone
 * @property {string|null} company
 * @property {UserRole} role
 * @property {boolean} is_staff
 * @property {string} created_at
 * @property {{access:string,refresh:string}} tokens
 */

/** @typedef {Object} LoginPayload
 * @property {string} email
 * @property {string} password
 */

/** @typedef {Object} LoginResponse
 * @property {string} access
 * @property {string} refresh
 * @property {{id:number,email:string,full_name:string,role:UserRole,is_staff:boolean}} user
 */

// ---------------------------------------------------------------------------
// Project — /api/projects/
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} Milestone
 * @property {number} id
 * @property {string} title
 * @property {string|null} [description]
 * @property {string|null} [due_date] YYYY-MM-DD
 * @property {boolean} is_completed
 * @property {number} [order]
 */

/**
 * @typedef {Object} Project
 * @property {number} id
 * @property {string} title
 * @property {string} slug
 * @property {string} description
 * @property {number|null} client FK → Client
 * @property {string|null} [client_name] denormalized for public
 * @property {ProjectStatus} status
 * @property {string} [status_display] e.g. "In Progress"
 * @property {number} progress 0–100
 * @property {string|null} [budget] decimal as string "85000.00"
 * @property {string} [currency] default "USD"
 * @property {string|null} [start_date] YYYY-MM-DD
 * @property {string|null} [end_date] YYYY-MM-DD
 * @property {string|null} [location]
 * @property {string|null} [cover_image] URL
 * @property {string[]} [gallery] image URLs
 * @property {boolean} is_published
 * @property {boolean} is_featured
 * @property {string} tracking_code e.g. "BT-2026-0012" (read-only)
 * @property {string} created_at
 * @property {string} updated_at
 * @property {Milestone[]} [milestones] detail view only
 */

/** @typedef {Object} ProjectCreatePayload @property {string} title @property {string} description @property {number|null} [client] @property {ProjectStatus} [status] @property {number} [progress] @property {string} [budget] @property {string} [currency] @property {string} [start_date] @property {string} [end_date] @property {string} [location] @property {boolean} [is_published] @property {boolean} [is_featured] */
/** @typedef {Object} ProjectUpdatePayload @property {ProjectStatus} [status] @property {number} [progress] — completing requires progress 100 (backend auto-sets) */

// ---------------------------------------------------------------------------
// Client — /api/clients/ (admin only)
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} Client
 * @property {number} id
 * @property {string} full_name
 * @property {string|null} [company]
 * @property {string|null} [email]
 * @property {string|null} [phone]
 * @property {string|null} [address]
 * @property {number|null} [user] FK → User
 * @property {string|null} [notes] internal only
 * @property {number} [projects_count] annotated
 * @property {number} [active_quotes_count] annotated
 * @property {string} created_at
 * @property {string} updated_at
 */

// ---------------------------------------------------------------------------
// Quote — /api/quotes/
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} Quote
 * @property {number} id
 * @property {string} tracking_id e.g. "Q-2026-0021" (read-only)
 * @property {string} full_name
 * @property {string} email
 * @property {string} phone
 * @property {ServiceType} service_type
 * @property {BudgetRange} budget_range
 * @property {string} message
 * @property {PreferredContact} preferred_contact
 * @property {string|null} [attachment_url]
 * @property {QuoteStatus} status
 * @property {string|null} [estimated_price] decimal string, admin-set
 * @property {string|null} [admin_notes] admin-only, excluded for clients
 * @property {string} created_at
 */

/** @typedef {Object} QuoteCreatePayload (public, no token)
 * @property {string} full_name @property {string} email @property {string} phone
 * @property {ServiceType} [service_type] @property {BudgetRange} [budget_range]
 * @property {string} message @property {PreferredContact} [preferred_contact]
 * @property {string} [attachment_url]
 */

// ---------------------------------------------------------------------------
// Contact — /api/contact/
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} ContactMessage
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {string|null} [phone]
 * @property {string} subject
 * @property {string} message
 * @property {boolean} is_read
 * @property {string} created_at
 */

/** @typedef {Object} ContactCreatePayload @property {string} name @property {string} email @property {string} [phone] @property {string} subject @property {string} message */

// ---------------------------------------------------------------------------
// Testimonial — /api/testimonials/
// ---------------------------------------------------------------------------

/**
 * @typedef {Object} Testimonial
 * @property {number} id
 * @property {string} client_name
 * @property {string|null} [company]
 * @property {number|null} [project] FK → Project
 * @property {string|null} [project_title] denormalized
 * @property {number} rating 1–5
 * @property {string} text 20–1000 chars
 * @property {string|null} [avatar] URL
 * @property {boolean} is_approved
 * @property {boolean} is_featured
 * @property {string} created_at
 */

/** @typedef {Object} TestimonialCreatePayload (public)
 * @property {string} client_name @property {string} [company] @property {number|null} [project]
 * @property {number} rating @property {string} text
 */

// ---------------------------------------------------------------------------
// Endpoint map (for api.js helpers)
// ---------------------------------------------------------------------------

export const ENDPOINTS = {
  register: "/api/auth/register/",
  login: "/api/auth/login/",
  refresh: "/api/auth/refresh/",
  me: "/api/auth/me/",
  projects: "/api/projects/",
  featuredProjects: "/api/projects/featured/",
  projectDetail: (id) => `/api/projects/${id}/`,
  clients: "/api/clients/",
  clientDetail: (id) => `/api/clients/${id}/`,
  quotes: "/api/quotes/",
  quoteDetail: (id) => `/api/quotes/${id}/`,
  quoteAccept: (id) => `/api/quotes/${id}/accept/`,
  contact: "/api/contact/",
  contactDetail: (id) => `/api/contact/${id}/`,
  testimonials: "/api/testimonials/",
  testimonialDetail: (id) => `/api/testimonials/${id}/`,
  pendingTestimonials: "/api/testimonials/pending/",
};

export const STATUS_TRANSITIONS = {
  quote: {
    new: ["contacted", "declined", "expired"],
    contacted: ["estimated", "declined", "expired"],
    estimated: ["accepted", "declined", "expired"],
    accepted: [],
    declined: [],
    expired: [],
  },
  project: {
    planned: ["in_progress", "cancelled"],
    in_progress: ["on_hold", "completed", "cancelled"],
    on_hold: ["in_progress", "cancelled"],
    completed: [],
    cancelled: [],
  },
};

export const STATUS_LABELS = {
  planned: "Scheduled",
  in_progress: "Under construction",
  on_hold: "Paused",
  completed: "Delivered",
  cancelled: "Cancelled",
  new: "New",
  contacted: "Contacted",
  estimated: "Estimated",
  accepted: "Accepted",
  declined: "Declined",
  expired: "Expired",
};
