import { useEffect, useState } from "react"
import { useNavigate } from "react-router"
import { BookOpen, Clock, CalendarDays, Mail, TrendingUp } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { getRequest } from "@/services"
import useStore from "@/store"

interface Syllabus {
    skill_id: number
    user_id: string
    email: string
    skill: string
    days: number
    hours: number
    created_at: string
    total_tasks: number
    completed_tasks: number
}

function SyllabusCard({ item, onClick }: { item: Syllabus; onClick: () => void }) {
    const progress = item.total_tasks > 0
        ? Math.round((item.completed_tasks / item.total_tasks) * 100)
        : 0

    const isCompleted = progress === 100
    const isInProgress = progress > 0 && progress < 100

    return (
        <Card
            className="relative overflow-hidden border border-border/60 bg-card hover:shadow-lg hover:border-border transition-all duration-300 cursor-pointer"
            onClick={onClick}
        >
            {/* top accent bar */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-violet-500 via-indigo-500 to-blue-500" />

            <CardHeader className="pb-3 pt-6">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                            <BookOpen className="h-5 w-5" />
                        </div>
                        <h3 className="text-lg font-semibold leading-tight">{item.skill}</h3>
                    </div>
                    <Badge
                        variant={isCompleted ? "default" : isInProgress ? "secondary" : "outline"}
                        className={
                            isCompleted
                                ? "bg-emerald-500/15 text-emerald-600 border-emerald-300 hover:bg-emerald-500/20"
                                : isInProgress
                                ? "bg-indigo-500/15 text-indigo-600 border-indigo-300 hover:bg-indigo-500/20"
                                : "text-muted-foreground"
                        }
                    >
                        {isCompleted ? "Completed" : isInProgress ? "In Progress" : "Not Started"}
                    </Badge>
                </div>
                <div className="flex items-center gap-1.5 text-sm text-muted-foreground mt-1 ml-11">
                    <Mail className="h-3.5 w-3.5 shrink-0" />
                    <span className="truncate">{item.email}</span>
                </div>
            </CardHeader>

            <CardContent className="space-y-4">
                {/* progress */}
                <div className="space-y-1.5">
                    <div className="flex justify-between text-xs text-muted-foreground">
                        <span className="flex items-center gap-1">
                            <TrendingUp className="h-3 w-3" />
                            Progress
                        </span>
                        <span className="font-medium text-foreground">{item.completed_tasks} / {item.total_tasks} days</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                    <p className="text-right text-xs font-semibold text-primary">{progress}%</p>
                </div>

                {/* stats */}
                <div className="grid grid-cols-2 gap-2">
                    <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2">
                        <CalendarDays className="h-4 w-4 text-muted-foreground" />
                        <div>
                            <p className="text-xs text-muted-foreground">Duration</p>
                            <p className="text-sm font-medium">{item.days} days</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2">
                        <Clock className="h-4 w-4 text-muted-foreground" />
                        <div>
                            <p className="text-xs text-muted-foreground">Daily</p>
                            <p className="text-sm font-medium">{item.hours} hr{item.hours !== 1 ? "s" : ""}</p>
                        </div>
                    </div>
                </div>

                {/* date */}
                {item.created_at && (
                    <p className="text-xs text-muted-foreground">
                        Started {new Date(item.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </p>
                )}
            </CardContent>
        </Card>
    )
}

function CardSkeleton() {
    return (
        <Card className="overflow-hidden border border-border/60">
            <div className="h-1 bg-muted" />
            <CardHeader className="pb-3 pt-6">
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                        <Skeleton className="h-9 w-9 rounded-lg" />
                        <Skeleton className="h-5 w-32" />
                    </div>
                    <Skeleton className="h-5 w-20 rounded-full" />
                </div>
                <Skeleton className="h-4 w-48 ml-11 mt-1" />
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-1.5">
                    <div className="flex justify-between">
                        <Skeleton className="h-3 w-16" />
                        <Skeleton className="h-3 w-20" />
                    </div>
                    <Skeleton className="h-2 w-full rounded-full" />
                </div>
                <div className="grid grid-cols-2 gap-2">
                    <Skeleton className="h-14 rounded-md" />
                    <Skeleton className="h-14 rounded-md" />
                </div>
                <Skeleton className="h-3 w-32" />
            </CardContent>
        </Card>
    )
}

export default function SyllabiPage() {
    const [syllabi, setSyllabi] = useState<Syllabus[]>([])
    const [loading, setLoading] = useState(true)
    const navigate = useNavigate()
    const { setPluginName, setPluginInfo } = useStore((state: any) => state)

    useEffect(() => {
        setPluginName("Syllabi")
        setPluginInfo("View all learning plans and their progress.")
    }, [setPluginName, setPluginInfo])

    useEffect(() => {
        async function fetchSyllabi() {
            const { success, data } = await getRequest("/py/syllabi")
            if (success) setSyllabi(data)
            setLoading(false)
        }
        fetchSyllabi()
    }, [])

    return (
        <div className="p-6 space-y-6">
            <div>
                <h1 className="text-2xl font-bold tracking-tight">Syllabi</h1>
                <p className="text-muted-foreground mt-1">All active learning plans and their progress</p>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {Array.from({ length: 6 }).map((_, i) => <CardSkeleton key={i} />)}
                </div>
            ) : syllabi.length === 0 ? (
                <Card className="flex flex-col items-center justify-center py-16 text-center border-dashed">
                    <BookOpen className="h-10 w-10 text-muted-foreground mb-3" />
                    <h3 className="font-semibold text-lg">No syllabi yet</h3>
                    <p className="text-muted-foreground text-sm mt-1">Subscribe a user and generate a syllabus to get started.</p>
                </Card>
            ) : (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {syllabi.map((item) => (
                        <SyllabusCard
                            key={item.skill_id}
                            item={item}
                            onClick={() => navigate(`/syllabi/${item.skill_id}`)}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}
