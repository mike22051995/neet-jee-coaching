interface Props {
  status: string
}

const statusConfig: Record<string, { label: string; className: string }> = {
  // Enrollment
  pending_payment: { label: 'Pending Payment', className: 'badge-yellow' },
  confirmed:       { label: 'Confirmed',        className: 'badge-green'  },
  cancelled:       { label: 'Cancelled',         className: 'badge-red'   },
  // Payment
  submitted:  { label: 'Under Review',  className: 'badge-blue'   },
  verified:   { label: 'Verified',      className: 'badge-green'  },
  rejected:   { label: 'Rejected',      className: 'badge-red'    },
  refunded:   { label: 'Refunded',      className: 'badge-gray'   },
  // Batch
  draft:            { label: 'Draft',            className: 'badge-gray'   },
  upcoming:         { label: 'Upcoming',         className: 'badge-blue'   },
  enrollment_open:  { label: 'Enrollment Open',  className: 'badge-green'  },
  running:          { label: 'Running',          className: 'badge-green'  },
  completed:        { label: 'Completed',        className: 'badge-gray'   },
  archived:         { label: 'Archived',         className: 'badge-gray'   },
}

export function StatusBadge({ status }: Props) {
  const config = statusConfig[status] || { label: status, className: 'badge-gray' }
  return <span className={config.className}>{config.label}</span>
}
