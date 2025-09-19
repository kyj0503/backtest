package com.webproject.backtest_be_spring.infrastructure.persistence.community;

import com.webproject.backtest_be_spring.domain.community.model.Post;
import com.webproject.backtest_be_spring.domain.community.model.PostCategory;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface JpaPostRepository extends JpaRepository<Post, Long> {

    Page<Post> findByDeletedFalse(Pageable pageable);

    Page<Post> findByCategoryAndDeletedFalse(PostCategory category, Pageable pageable);

    @Query("select p from Post p where p.deleted = false and (lower(p.title) like lower(concat('%', :keyword, '%')) "
            + "or lower(p.content) like lower(concat('%', :keyword, '%')))")
    Page<Post> search(@Param("keyword") String keyword, Pageable pageable);

    Optional<Post> findByIdAndDeletedFalse(Long id);

    long countByDeletedFalse();

    @Modifying(clearAutomatically = true)
    @Query("update Post p set p.viewCount = p.viewCount + 1 where p.id = :postId")
    void incrementViewCount(@Param("postId") Long postId);

    @Modifying(clearAutomatically = true)
    @Query("update Post p set p.likeCount = p.likeCount + :delta where p.id = :postId")
    void adjustLikeCount(@Param("postId") Long postId, @Param("delta") long delta);

    @Modifying(clearAutomatically = true)
    @Query("update Post p set p.commentCount = p.commentCount + :delta where p.id = :postId")
    void adjustCommentCount(@Param("postId") Long postId, @Param("delta") long delta);
}
