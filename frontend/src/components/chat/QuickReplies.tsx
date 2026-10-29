import type { QuickReply } from '../../types/chat'

interface Props {
  replies: QuickReply[]
  disabled?: boolean
  onSelect: (reply: QuickReply) => void
}

export function QuickReplies({ replies, disabled, onSelect }: Props) {
  if (!replies.length) return null
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {replies.map((r) => (
        <button
          key={r.id}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(r)}
          className="rounded-full border border-green-200 bg-white px-3 py-1.5 text-xs font-medium text-green-800 shadow-sm transition hover:bg-green-50 disabled:opacity-50"
        >
          {r.label}
        </button>
      ))}
    </div>
  )
}
