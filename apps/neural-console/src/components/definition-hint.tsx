import { CircleHelpIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'

export function DefinitionHint({
  label,
  definition,
}: {
  label: string
  definition: string
}) {
  return (
    <TooltipProvider delay={120} closeDelay={0}>
      <Tooltip>
        <TooltipTrigger
          render={
            <Button
              type="button"
              variant="ghost"
              size="icon-xs"
              className="text-muted-foreground"
              aria-label={`${label}: ${definition}`}
            />
          }
        >
          <CircleHelpIcon />
        </TooltipTrigger>
        <TooltipContent>{definition}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
